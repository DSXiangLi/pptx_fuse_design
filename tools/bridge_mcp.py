#!/usr/bin/env python3
"""Official MCP SDK stdio proxy for the editor/agent bridge daemon."""
from __future__ import annotations

import asyncio
import contextlib
import json
import sys
import uuid
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class CheckEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Literal["render", "capacity", "images", "manifest", "export"]
    argv: Annotated[list[Annotated[str, Field(min_length=1)]], Field(min_length=1)]
    exit_code: int
    report_path: str | None


class ValidationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_revision: Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
    checks: Annotated[list[CheckEvidence], Field(min_length=1)]
    export_source_revision: Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")] | None = None

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.fastmcp.exceptions import ToolError
except ImportError as exc:
    print("缺少官方 MCP SDK；请安装 mcp>=1.28,<2（手动编辑器不需要此依赖）", file=sys.stderr)
    raise SystemExit(3) from exc

from bridge_core import BridgeError, admin_request, ensure_daemon


class BridgeMCP:
    def __init__(self, workdir: str, *, allow_convert=False):
        self.workdir = str(Path(workdir).resolve())
        self.consumer_id = str(uuid.uuid4())
        self.discovery = ensure_daemon(self.workdir, allow_convert=allow_convert)
        self.owned_sessions: set[str] = set()
        self._stop = asyncio.Event()

        @contextlib.asynccontextmanager
        async def lifespan(_server):
            task = asyncio.create_task(self._heartbeat())
            try:
                yield {}
            finally:
                self._stop.set()
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        self.mcp = FastMCP(
            name="pptx-html-bridge",
            instructions="Open an editor task, await explicit browser intents, modify only the assigned work_path, validate, then push an update.",
            log_level="ERROR",
            lifespan=lifespan,
        )
        self._register()

    async def _request(self, path: str, body: dict, timeout=130):
        try:
            return await asyncio.to_thread(admin_request, self.discovery, path, body, timeout)
        except BridgeError as exc:
            raise ToolError(json.dumps(exc.payload(), ensure_ascii=False, separators=(",", ":"))) from exc
        except Exception as exc:
            raise ToolError(json.dumps({"ok":False,"error":{"code":"STORAGE_UNAVAILABLE","message":"bridge daemon unavailable","retryable":True,"details":{}}},separators=(",", ":"))) from exc

    def _register(self):
        @self.mcp.tool(description="Open or reuse one managed editor task in the configured workdir. Registers this MCP consumer and may initialize the task's isolated Git protection ref. Returns a browser URL containing only a session-scoped browser credential. Does not acquire queue ownership or publish files.")
        async def open_editor(
            deck_path: str | None = None,
            output_path: str = "index.html",
            view: Literal["edit", "brief", "annotate", "export"] = "edit",
            open_browser: bool = True,
        ) -> dict[str, object]:
            result = await self._request("/api/bridge/open", {"consumer_id":self.consumer_id,"deck_path":deck_path,"output_path":output_path,"view":view,"open_browser":open_browser})
            self.owned_sessions.add(result["session_id"])
            return result

        @self.mcp.tool(description="Atomically acquire this registered consumer's session lease and wait for the earliest pending browser intent. Timeout is bounded to 1-120 seconds. A claimed intent is redelivered until explicitly completed or failed; cancellation only stops this wait and never deletes an intent.")
        async def await_intent(
            session_id: Annotated[str, Field(min_length=1)],
            timeout_sec: Annotated[int, Field(ge=1, le=120)] = 25,
        ) -> dict[str, object]:
            return await self._request("/api/bridge/await", {"session_id":session_id,"consumer_id":self.consumer_id,"timeout_sec":timeout_sec}, timeout=timeout_sec+10)

        @self.mcp.tool(description="Report progress, fail the current attempt, or complete it. Complete publishes only the daemon-assigned attempt work copy after ownership, revision, exact validation evidence, artifact and journal checks. It never accepts arbitrary source paths or shell commands. Successful complete retries return the original persisted receipt.")
        async def push_update(
            session_id: Annotated[str, Field(min_length=1)],
            intent_id: Annotated[str, Field(min_length=1)],
            attempt: Annotated[int, Field(ge=1)],
            action: Literal["progress", "complete", "fail"],
            message: Annotated[str, Field(max_length=2000)] = "",
            validation: ValidationEvidence | None = None,
        ) -> dict[str, object]:
            evidence = (validation.model_dump(exclude={"export_source_revision"} if validation.export_source_revision is None else set())
                        if validation is not None else None)
            return await self._request("/api/bridge/update", {"session_id":session_id,"intent_id":intent_id,"attempt":attempt,"consumer_id":self.consumer_id,"action":action,"message":message,"validation":evidence})

        @self.mcp.tool(description="Read persistent task, revision, export freshness, browser, queue, recovery and capability state. This is read-only and does not register or acquire a consumer lease.")
        async def get_status(session_id: Annotated[str, Field(min_length=1)]) -> dict[str, object]:
            return await self._request("/api/bridge/status", {"session_id":session_id})

        @self.mcp.tool(description="Pause only this MCP consumer, interrupt its unfinished attempt, release its owner lease, and require a later explicit open_editor before awaiting again. It does not stop the daemon or browser and does not delete pending work, drafts, history or files.")
        async def close_session(
            session_id: Annotated[str, Field(min_length=1)],
            reason: Annotated[str, Field(max_length=2000)] = "user-ended",
        ) -> dict[str, object]:
            result = await self._request("/api/bridge/close", {"session_id":session_id,"consumer_id":self.consumer_id,"reason":reason})
            self.owned_sessions.discard(session_id)
            return result

    async def _heartbeat(self):
        while not self._stop.is_set():
            await asyncio.sleep(15)
            for session_id in tuple(self.owned_sessions):
                try:
                    await self._request("/api/bridge/heartbeat", {"protocol_version":2,"role":"consumer","session_id":session_id,"consumer_id":self.consumer_id}, timeout=5)
                except ToolError:
                    pass

    def run(self):
        self.mcp.run(transport="stdio")


def run(workdir: str, *, allow_convert=False):
    BridgeMCP(workdir, allow_convert=allow_convert).run()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: bridge_mcp.py WORKDIR", file=sys.stderr)
        raise SystemExit(2)
    run(sys.argv[1])
