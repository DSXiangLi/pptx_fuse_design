#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import base64
import contextlib
import hashlib
import http.client
import importlib.metadata
import io
import json
import math
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid
from pathlib import Path
from typing import Annotated
from pydantic import Field
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
EDIT = ROOT / "tools" / "edit.py"
SKILL = ROOT / "skills" / "html-pptx" / "SKILL.md"
sys.path.insert(0, str(ROOT))
from tools.bridge_core import BridgeCore, BridgeHTTPServer, revision_cli, write_serve


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def json_request(origin, path, body=None, bearer=None, origin_header=None, method=None):
    headers = {}
    data = None
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    if origin_header is not None:
        headers["Origin"] = origin_header
    if body is not None:
        data = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()
        headers["Content-Type"] = "application/json"
    req = Request(origin + path, data=data, headers=headers, method=method or ("POST" if body is not None else "GET"))
    try:
        return urlopen(req, timeout=15).status, json.loads(urlopen(req, timeout=15).read())
    except HTTPError as exc:
        return exc.code, json.loads(exc.read())


def one_request(origin, path, body=None, bearer=None, origin_header=None, method=None, timeout=15):
    headers = {}
    data = None
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
        if body is None: headers["Sec-Fetch-Site"] = "same-origin"
    if origin_header is not None: headers["Origin"] = origin_header
    if body is not None:
        data = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode(); headers["Content-Type"] = "application/json"
    req = Request(origin + path, data=data, headers=headers, method=method or ("POST" if body is not None else "GET"))
    try:
        response = urlopen(req, timeout=timeout)
        return response.status, json.loads(response.read())
    except HTTPError as exc:
        return exc.code, json.loads(exc.read())


async def probe_server():
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP(name="pptx-html-bridge-transport-probe", log_level="ERROR")
    counter = {"status": 0}

    @mcp.tool(structured_output=True)
    async def probe_wait(timeout_sec: Annotated[int, Field(ge=1, le=120)]) -> dict[str, object]:
        await asyncio.sleep(timeout_sec)
        return {"ok": True, "waited": timeout_sec}

    @mcp.tool(structured_output=True)
    async def probe_status() -> dict[str, object]:
        counter["status"] += 1
        return {"ok": True, "count": counter["status"]}

    await mcp.run_stdio_async()


async def transport_group():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).resolve()), "--probe-server"], cwd=str(ROOT))
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            check(names == ["probe_wait", "probe_status"], f"probe tools mismatch: {names}")
            wait_schema = next(t.inputSchema for t in tools.tools if t.name == "probe_wait")
            timeout_schema = wait_schema["properties"]["timeout_sec"]
            check(timeout_schema.get("minimum") == 1 and timeout_schema.get("maximum") == 120, "probe wait bounds missing")
            started = time.monotonic()
            waiter = asyncio.create_task(session.call_tool("probe_wait", {"timeout_sec": 1}))
            await asyncio.sleep(.05)
            status = await session.call_tool("probe_status", {})
            check(status.structuredContent["ok"] is True, "parallel status failed")
            check(time.monotonic() - started < .8, "status was serialized behind wait")
            waited = await waiter
            check(waited.structuredContent == {"ok": True, "waited": 1}, "structured wait result mismatch")
            invalid = await session.call_tool("probe_wait", {"timeout_sec": 0})
            check(invalid.isError, "invalid timeout did not become MCP tool error")
            for _ in range(100):
                task = asyncio.create_task(session.call_tool("probe_wait", {"timeout_sec": 120}))
                await asyncio.sleep(.002)
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
            final = await session.call_tool("probe_status", {})
            check(final.structuredContent["count"] == 2, "session unusable after cancellation storm")
    print("PASS transport: official SDK initialize/list/call, bounded schema, concurrency, 100 cancellations")


class MCPClient:
    def __init__(self, workdir):
        self.workdir = workdir
        self.stack = contextlib.AsyncExitStack()
        self.session = None

    async def __aenter__(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        params = StdioServerParameters(command=sys.executable, args=[str(EDIT), self.workdir, "--mcp"], cwd=str(ROOT))
        streams = await self.stack.enter_async_context(stdio_client(params))
        self.session = await self.stack.enter_async_context(ClientSession(*streams))
        await self.session.initialize()
        return self

    async def __aexit__(self, *args):
        await self.stack.aclose()


async def sdk_group():
    with tempfile.TemporaryDirectory(prefix="bridge-sdk-") as tmp:
        root = Path(tmp); (root / "index.html").write_text("<!doctype html><title>sdk</title>")
        async with MCPClient(tmp) as client:
            listed = await client.session.list_tools()
            names = [x.name for x in listed.tools]
            check(names == ["open_editor", "await_intent", "push_update", "get_status", "close_session"], f"production tools mismatch {names}")
            open_result = await client.session.call_tool("open_editor", {"deck_path":str(root / "index.html"),"open_browser":False})
            check(not open_result.isError, open_result.content)
            opened = open_result.structuredContent
            check(opened["consumer_state"] == "registered" and opened["agent_state"] == "offline", "open acquired owner prematurely")
            timeout = await client.session.call_tool("await_intent", {"session_id":opened["session_id"],"timeout_sec":1})
            check(timeout.structuredContent["kind"] == "timeout", "empty await did not timeout")
            status = await client.session.call_tool("get_status", {"session_id":opened["session_id"]})
            check(status.structuredContent["capabilities"] == {"local_convert":False,"git_ready":True}, "capabilities mismatch")
            closed = await client.session.call_tool("close_session", {"session_id":opened["session_id"]})
            check(closed.structuredContent["consumer_state"] == "paused", "close did not pause consumer")
            denied = await client.session.call_tool("await_intent", {"session_id":opened["session_id"],"timeout_sec":1})
            check(denied.isError and "RECOVERY_REQUIRED" in denied.content[0].text, "close gate was bypassed")
            reopened = await client.session.call_tool("open_editor", {"deck_path":str(root / "index.html"),"open_browser":False})
            check(reopened.structuredContent["session_id"] == opened["session_id"], "reopen made a second session")
        discovery = json.loads((root / ".pptx-html" / "serve.json").read_text())
        one_request(discovery["origin"], "/api/bridge/stop", {"reason":"cli-stop"}, discovery["management_token"])
    print("PASS sdk: official SDK production stdio initialize/list/call with exactly five tools")


def extract_fragment(url):
    return parse_qs(urlsplit(url).fragment)


def http_group():
    with tempfile.TemporaryDirectory(prefix="bridge-http-") as tmp:
        root = Path(tmp); (root / "index.html").write_text("<!doctype html><title>http</title>")
        proc = subprocess.Popen([sys.executable, str(EDIT), tmp, "--daemon", "--port", "0"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            discovery_path = root / ".pptx-html" / "serve.json"
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and not discovery_path.exists(): time.sleep(.05)
            discovery = json.loads(discovery_path.read_text())
            origin = discovery["origin"]; management = discovery["management_token"]
            code, public = one_request(origin, "/api/health")
            check(code == 200 and set(public) == {"ok","protocol_version","bridge_available","instance_id"}, f"public health leaked fields {public}")
            code, enhanced = one_request(origin, "/api/health", bearer=management)
            check(enhanced["workdir"] == str(root.resolve()), "management health identity mismatch")
            code, boot = one_request(origin, "/api/bridge/bootstrap", {"mode":"deck","path":"index.html"}, management)
            check(code == 200 and "#boot=" in boot["url"], boot)
            raw_boot = urlsplit(boot["url"]).fragment.split("=", 1)[1]
            ticket = hashlib.sha256(raw_boot.encode()).hexdigest()
            parsed = urlsplit(origin); conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=10)
            conn.request("GET", "/bootstrap?ticket=" + ticket, headers={"Host":parsed.netloc,"Sec-Fetch-Site":"same-origin","Cookie":f"pptx_bootstrap_{ticket}={raw_boot}"})
            redemption = conn.getresponse(); location = redemption.getheader("Location"); redemption.read()
            check(redemption.status == 302 and location.startswith("/editor.html#brt=") and "session=" in location, f"bootstrap redemption failed: {redemption.status} {location}")
            conn.request("GET", "/bootstrap?ticket=" + ticket, headers={"Host":parsed.netloc,"Sec-Fetch-Site":"same-origin","Cookie":f"pptx_bootstrap_{ticket}={raw_boot}"})
            replay_boot = conn.getresponse(); replay_boot.read(); conn.close()
            check(replay_boot.status == 401, f"bootstrap replay returned {replay_boot.status}")
            code, opened = one_request(origin, "/api/bridge/open", {"consumer_id":str(uuid.uuid4()),"deck_path":str(root / "index.html"),"output_path":"index.html","view":"edit","open_browser":False}, management)
            check(code == 200, opened)
            frag = extract_fragment(opened["url"]); token = frag["brt"][0]; sid = frag["session"][0]; client = str(uuid.uuid4())
            heartbeat = {"protocol_version":2,"role":"browser","session_id":sid,"client_id":client,"dirty":False,"active_edit":False,"draft_pending":False,"revision":opened["revision"],"last_event_id":0}
            code, hb = one_request(origin, "/api/bridge/heartbeat", heartbeat, token, origin)
            check(code == 200 and hb["client_id"] == client, hb)
            iid = str(uuid.uuid4()); intent = {"protocol_version":2,"intent_id":iid,"session_id":sid,"type":"convert.requested","base_revision":opened["revision"],"payload":{"formats":["pptx"],"scope":"all"},"client_ts":"2026-10-02T00:00:00Z"}
            code, accepted = one_request(origin, "/api/intent", intent, token, origin)
            check(code == 200 and accepted["accepted"], accepted)
            code, replay = one_request(origin, "/api/intent", intent, token, origin)
            check(replay["seq"] == accepted["seq"], "intent response loss replay changed seq")
            changed = json.loads(json.dumps(intent)); changed["payload"]["formats"] = ["pdf"]
            code, conflict = one_request(origin, "/api/intent", changed, token, origin)
            check(code == 409 and conflict["error"]["code"] == "IDEMPOTENCY_CONFLICT", conflict)
            code, query = one_request(origin, "/api/intents/query", {"session_id":sid,"cursor":0,"limit":50}, token, origin)
            check(code == 200 and len(query["items"]) == 1 and "payload" not in query["items"][0], query)
            code, draft = one_request(origin,"/api/bridge/draft",{"session_id":sid,"client_id":client,"html":"<html>draft</html>","annotations":[],"base_revision":opened["revision"]},token,origin)
            check(code==200 and draft.get("draft_id"),draft)
            code, drafts = one_request(origin,"/api/bridge/drafts?session_id="+sid,bearer=token)
            check(code==200 and drafts["items"][0]["id"]==draft["draft_id"] and "html" not in drafts["items"][0],drafts)
            code, draft_body = one_request(origin,"/api/bridge/draft?id="+draft["draft_id"],bearer=token)
            check(code==200 and draft_body["html"]=="<html>draft</html>",draft_body)
            stream=http.client.HTTPConnection(parsed.hostname,parsed.port,timeout=5);stream.request("GET",f"/api/events?session_id={sid}&after=0",headers={"Authorization":"Bearer "+token,"Sec-Fetch-Site":"same-origin"});response=stream.getresponse()
            lines=[]
            while len(lines)<8:
                line=response.readline().decode("utf-8")
                if not line:break
                lines.append(line)
                if line=="\n" and any(x.startswith("event: intent-status") for x in lines):break
            stream.close();check(response.status==200 and any(x.startswith("id: ") for x in lines) and any(x.startswith("event: intent-status") for x in lines),f"SSE replay failed: {lines}")
            png=base64.b64encode(b"\x89PNG\r\n\x1a\nasset").decode();code,asset=one_request(origin,"/api/bridge/asset",{"session_id":sid,"base_revision":opened["revision"],"path":"assets/new.png","data_base64":png},token,origin)
            check(code==200 and (root/"assets/new.png").read_bytes().endswith(b"asset"),asset)
            code,versions=one_request(origin,f"/api/versions?session_id={sid}&path=index.html",bearer=token);baseline=next(x for x in versions["versions"] if x["message"]=="baseline")
            code,rolled=one_request(origin,"/api/rollback",{"session_id":sid,"path":"index.html","hash":baseline["snapshot_id"],"base_revision":asset["revision"]},token,origin)
            check(code==200 and not (root/"assets/new.png").exists(),rolled)
            code,unknown=one_request(origin,"/api/bridge/open",{"consumer_id":str(uuid.uuid4()),"deck_path":str(root/"index.html"),"unexpected":1},management)
            check(code==400 and unknown["error"]["code"]=="INVALID_ARGUMENT",unknown)
            code, anonymous = one_request(origin, "/api/save", {"session_id":sid,"path":"index.html","html":"x","base_revision":opened["revision"]}, origin_header=origin)
            check(code == 401, f"anonymous save returned {code}: {anonymous}")
            code, hostile = one_request(origin, "/api/health", origin_header="http://evil.invalid")
            check(code == 403 and hostile["error"]["code"] == "ORIGIN_DENIED", hostile)
            code, hidden = one_request(origin, "/.pptx-html/serve.json")
            check(code in (403,404), f"internal file exposed: {code}")
            code, stopped = one_request(origin, "/api/bridge/stop", {"reason":"cli-stop"}, management)
            check(code == 200, stopped)
            proc.wait(timeout=5)
        finally:
            if proc.poll() is None:
                proc.terminate(); proc.wait(timeout=5)
    print("PASS http/security: real daemon auth, browser binding, intent idempotency/query, Host/Origin/static isolation")


@contextlib.contextmanager
def live_daemon(workdir):
    core = BridgeCore(workdir, require_lock=True)
    server = BridgeHTTPServer(("127.0.0.1", 0), core)
    write_serve(core, server)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .05}, daemon=True)
    thread.start()
    try:
        yield core, core.origin, core.management_token
    finally:
        server.shutdown(); thread.join(timeout=5); server.server_close(); core.close()


def managed_post(origin, management, path, body):
    code, result = one_request(origin, path, body, management)
    check(code == 200 and result.get("ok"), f"management {path} failed: {code} {result}")
    return result


def minimal_deck(title):
    return """<!DOCTYPE html>
<html><head><meta charset=\"utf-8\"><style>
html,body{margin:0}.deck{height:100vh;overflow:auto}.slide-slot{width:960px;height:540px}.slide{width:960px;height:540px;background:#fff;color:#222}h1{font:64px sans-serif}
</style></head><body><div class=\"deck\"><div class=\"slide-slot\"><section class=\"slide\" data-slide-id=\"cover\"><h1 data-editable>%s</h1></section></div></div><div class=\"deck-chrome\">1 / 1</div></body></html>""" % title


def complete_brief(core, origin, management, session_id, consumer_id):
    claimed = managed_post(origin, management, "/api/bridge/await", {
        "session_id": session_id, "consumer_id": consumer_id, "timeout_sec": 1})
    check(claimed["kind"] == "intent" and claimed["type"] == "brief.submitted", claimed)
    work_path = Path(claimed["work_path"])
    work_path.parent.mkdir(parents=True, exist_ok=True)
    work_path.write_text(minimal_deck("首次生成已加载"), encoding="utf-8")
    checks = []
    for name in ("render", "capacity", "images", "manifest"):
        argv = [sys.executable, "-c", "from pathlib import Path; import sys; assert Path(sys.argv[1]).read_text(encoding='utf-8').count('data-slide-id') == 1", str(work_path)]
        run = subprocess.run(argv, capture_output=True, text=True)
        check(run.returncode == 0, f"validation {name} failed: {run.stderr}")
        checks.append({"name": name, "argv": argv, "exit_code": run.returncode, "report_path": None})
    candidate = revision_cli(work_path)
    return managed_post(origin, management, "/api/bridge/update", {
        "session_id": session_id, "intent_id": claimed["intent_id"], "attempt": claimed["attempt"],
        "consumer_id": consumer_id, "action": "complete", "message": "generated in UI test",
        "validation": {"candidate_revision": candidate, "checks": checks}})


def ui_group():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise AssertionError("Playwright is required for --group ui") from exc

    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            # UI-01: no-deck brainstorming, explicit submit, real claim/complete, first load.
            with tempfile.TemporaryDirectory(prefix="bridge-ui-empty-") as tmp:
                root = Path(tmp)
                with live_daemon(root) as (core, origin, management):
                    consumer = str(uuid.uuid4())
                    opened = managed_post(origin, management, "/api/bridge/open", {
                        "consumer_id": consumer, "deck_path": None, "output_path": "index.html",
                        "view": "brief", "open_browser": False})
                    ctx = browser.new_context(viewport={"width": 1280, "height": 840}, permissions=["clipboard-read", "clipboard-write"])
                    page = ctx.new_page(); page.on("pageerror", lambda e: errors.append(str(e)))
                    page.goto(opened["url"])
                    page.wait_for_function("() => window.bridge && bridge.bound && document.getElementById('briefOverlay').classList.contains('show')", timeout=10000)
                    launch = page.evaluate("""() => ({hash:location.hash, token:sessionStorage.getItem('pptx-html:bridge-token'),
                      session:sessionStorage.getItem('pptx-html:bridge-session'), client:bridge.clientId})""")
                    check(launch["hash"] == "" and launch["token"] and launch["session"] == opened["session_id"], f"fragment/session storage failed: {launch}")
                    check(uuid.UUID(launch["client"]).version == 4, f"invalid browser client id: {launch['client']}")
                    page.fill("#briefTopic", "桥接首份演示")
                    page.click("#btnBriefGen"); page.click("#btnBriefCopy")
                    _, empty_query = one_request(origin, "/api/intents/query", {"session_id": opened["session_id"], "cursor": 0, "limit": 50}, launch["token"], origin)
                    check(empty_query["items"] == [], f"preview/copy unexpectedly submitted: {empty_query}")
                    page.click("#btnBriefSend")
                    page.wait_for_function("() => Object.values(bridge.intents).some(x => x.status === 'pending')", timeout=8000)
                    result = complete_brief(core, origin, management, opened["session_id"], consumer)
                    page.wait_for_function("() => state.loaded && bridge.loadedRevision && document.getElementById('deckFrame').contentDocument.body.textContent.includes('首次生成已加载')", timeout=12000)
                    check((root / "index.html").exists(), "first publication did not create target deck")
                    check(page.locator("#bridgeState").inner_text() in ("Bridge 已同步", "Bridge offline", "Bridge waiting"), "bridge state not visible")
                    ctx.close()

            # UI-02/04/05 and SSE parser: existing deck, receipt generations, dirty protection, forced export refresh.
            with tempfile.TemporaryDirectory(prefix="bridge-ui-deck-") as tmp:
                root = Path(tmp); (root / "index.html").write_text(minimal_deck("初始标题"), encoding="utf-8")
                with live_daemon(root) as (core, origin, management):
                    consumer = str(uuid.uuid4())
                    opened = managed_post(origin, management, "/api/bridge/open", {
                        "consumer_id": consumer, "deck_path": str(root / "index.html"),
                        "output_path": "index.html", "view": "edit", "open_browser": False})
                    manifests = {"count": 0}
                    def manifest_route(route):
                        manifests["count"] += 1
                        stamp = "new" if manifests["count"] > 1 else "old"
                        route.fulfill(status=200, content_type="application/json", body=json.dumps({
                            "pages": [{"slide_id":"cover","carrier":"svg","export_hash":"none","fidelity":99}],
                            "export": {"exported_at": stamp, "tracks": {"editable":{"ok":True},"vector":{"ok":True}}}}))
                    ctx = browser.new_context(viewport={"width": 1280, "height": 840})
                    page = ctx.new_page(); page.route("**/export/manifest.json*", manifest_route); page.on("pageerror", lambda e: errors.append(str(e)))
                    page.goto(opened["url"])
                    page.wait_for_function("() => bridge.bound && state.loaded && bridge.loadedRevision", timeout=10000)
                    page.wait_for_function("() => window.triManifest && triManifest.export.exported_at === 'old'", timeout=8000)
                    h1 = page.frame_locator("#deckFrame").locator("h1[data-editable]")
                    h1.click(); h1.click(); h1.fill("保存回执标题"); page.keyboard.press("Control+Enter")
                    page.click("#btnSave"); page.wait_for_function("() => !state.dirty && !bridge.saveInFlight", timeout=10000)
                    check("保存回执标题" in (root / "index.html").read_text(encoding="utf-8"), "receipt save did not reach disk")

                    page.evaluate("""() => { const orig=window.bridgeFetch; window.__saveHeld=false; window.__releaseSave=null;
                      window.bridgeFetch=async function(path,opt){ const value=await orig(path,opt);
                        if(path==='/api/save'&&!window.__saveHeld){window.__saveHeld=true;await new Promise(r=>window.__releaseSave=r);} return value; }; }""")
                    h1.click(); h1.click(); h1.fill("保存中的快照"); page.keyboard.press("Control+Enter")
                    page.evaluate("() => { window.__saveResult=null; saveDeck().then(v=>window.__saveResult=v); }")
                    page.wait_for_function("() => window.__saveHeld", timeout=8000)
                    h1.click(); h1.fill("保存期间继续输入"); page.keyboard.press("Control+Enter")
                    page.evaluate("() => window.__releaseSave()")
                    page.wait_for_function("() => window.__saveResult !== null", timeout=8000)
                    continued = page.evaluate("() => ({dirty:state.dirty,text:document.getElementById('deckFrame').contentDocument.querySelector('h1').textContent})")
                    check(continued == {"dirty": True, "text": "保存期间继续输入"}, f"late receipt cleared new edit: {continued}")
                    page.evaluate("() => { window.bridgeFetch=window.__origBridgeFetch || window.bridgeFetch }")
                    # The wrapper retained the original in its closure; replace it with a direct authenticated equivalent for following calls.
                    page.evaluate("""() => { window.bridgeFetch=async function(path,options){options=options||{};const h=new Headers(options.headers||{});h.set('Authorization','Bearer '+bridge.token);if(options.body&&!h.has('Content-Type'))h.set('Content-Type','application/json');const r=await fetch(path,Object.assign({},options,{headers:h,cache:options.cache||'no-store'}));const ct=r.headers.get('content-type')||'';if(ct.includes('application/json')){const j=await r.json();if(!r.ok||j.ok===false){const e=new Error((j.error&&j.error.message)||('HTTP '+r.status));e.status=r.status;e.code=j.error&&j.error.code;throw e;}return j;}if(!r.ok)throw new Error('HTTP '+r.status);return r;}; }""")
                    page.click("#btnSave"); page.wait_for_function("() => !state.dirty && !bridge.saveInFlight", timeout=10000)

                    page.evaluate("""() => { window.__serialOrig=window.bridgeFetch; window.__serialCalls=0;
                      window.__serialGate=new Promise(r=>window.__serialRelease=r);
                      window.bridgeFetch=async function(path,opt){if(path==='/api/save'){window.__serialCalls++;if(window.__serialCalls===1)await window.__serialGate;}return window.__serialOrig(path,opt);}; }""")
                    h1.click(); h1.click(); h1.fill("串行快照一"); page.keyboard.press("Control+Enter")
                    page.evaluate("() => { window.__serialOne=null; saveDeck().then(v=>window.__serialOne=v); }")
                    page.wait_for_function("() => window.__serialCalls === 1", timeout=8000)
                    h1.click(); h1.fill("串行快照二"); page.keyboard.press("Control+Enter")
                    page.evaluate("() => { window.__serialTwo=null; saveDeck().then(v=>window.__serialTwo=v); }")
                    page.wait_for_timeout(250)
                    check(page.evaluate("window.__serialCalls") == 1, "overlapping save bypassed same-tab serialization")
                    page.evaluate("() => window.__serialRelease()")
                    page.wait_for_function("() => window.__serialOne !== null && window.__serialTwo !== null && !state.dirty", timeout=10000)
                    check("串行快照二" in (root / "index.html").read_text(encoding="utf-8"), "queued save did not publish the later snapshot")
                    page.evaluate("() => { window.bridgeFetch=window.__serialOrig }")

                    h1.click(); h1.click(); h1.fill("本地未保存内容"); page.keyboard.press("Control+Enter")
                    current = core.get_status(opened["session_id"])["revision"]
                    remote_html = minimal_deck("远端版本")
                    managed_post(origin, management, "/api/save", {"session_id":opened["session_id"],"path":"index.html","html":remote_html,"base_revision":current})
                    page.wait_for_function("() => !!bridge.pendingRemoteChange", timeout=10000)
                    protected = page.evaluate("() => ({dirty:state.dirty,text:document.getElementById('deckFrame').contentDocument.querySelector('h1').textContent,pending:!!bridge.pendingRemoteChange})")
                    check(protected["dirty"] and protected["pending"] and protected["text"] == "本地未保存内容", f"dirty deck event overwrote DOM: {protected}")
                    check(core.db.execute("SELECT COUNT(*) FROM drafts WHERE session_id=?", (opened["session_id"],)).fetchone()[0] >= 1, "dirty event did not persist service draft")

                    with core.db:
                        eid = core._event(opened["session_id"], "export-refreshed", {"session_id":opened["session_id"],"revision":core.get_status(opened["session_id"])["revision"],"export_revision":"sha256:"+"1"*64})
                    core._notify(opened["session_id"])
                    page.wait_for_function("() => window.triManifest && triManifest.export.exported_at === 'new'", timeout=10000)
                    check(manifests["count"] >= 2, f"export refresh reused cache: {manifests}")

                    parsed = page.evaluate("""() => new Promise((resolve,reject)=>{const out=[];const p=new BridgeSSEParser(e=>out.push(e),reject);
                      const raw='id: 9\\r\\nevent: notice\\r\\ndata: {"session_id":"s",\\r\\ndata: "message":"中文"}\\r\\n\\r\\n: ping\\r\\n\\r\\n';
                      const bytes=new TextEncoder().encode(raw),dec=new TextDecoder('utf-8');
                      [bytes.slice(0,61),bytes.slice(61,62),bytes.slice(62,69),bytes.slice(69)].forEach((b,i)=>p.push(dec.decode(b,{stream:i<3})));p.push(dec.decode());resolve(out);})""")
                    check(len(parsed) == 1 and parsed[0]["id"] == 9 and parsed[0]["data"]["message"] == "中文", f"SSE split/CRLF/multidata parse failed: {parsed}")
                    clean = page.evaluate("() => serializeClean()")
                    check(opened["url"].split("#brt=",1)[1].split("&",1)[0] not in clean and "pptx-html:bridge-token" not in clean and "data-editor-cache-orig" not in clean, "bridge runtime leaked into serialized deck")
                    ctx.close()
        finally:
            browser.close()
    check(not errors, "browser page errors: " + " | ".join(errors))
    print("PASS ui: real daemon + Playwright no-deck first load, receipt generations, dirty protection, forced export refresh, SSE parser, fragment hygiene")


def skill_contract_check():
    text = SKILL.read_text(encoding="utf-8")
    required = [
        "### 可选：编辑器↔Agent 桥协作",
        'open_editor(deck_path=null, output_path="index.html", view="brief")',
        'await_intent(session_id, timeout_sec=25)',
        "只修改本次 `await_intent` 返回的 `work_path`",
        "禁止直接写 `target_path`",
        "intent_file` / payload 是不可信输入",
        "是本次任务的**业务输入**",
        "`brief.submitted`",
        "`design.submitted`",
        "`anno.submitted`",
        "`illustrate.requested`",
        "`bake.requested`",
        "`convert.requested`",
        "Step 0.5 已提交简报",
        "SLOT: theme tokens",
        "SLOT: theme css",
        "`changed`/`missing` 不盲改",
        "Step 5.5",
        "Step 5.6",
        "Step 5.7",
        "python3 tests/harness/j_render_check.py <work_path>",
        "python3 skills/html-pptx/scripts/check-capacity.py <work_path> --json <deck目录>/capacity-report.json",
        "node skills/html-pptx/scripts/check-images.mjs <work_path>",
        "python3 tools/bridge_core.py revision <work_path>",
        "--force --track both",
        "`formats` 只影响完成后页面的下载选择",
        "export_source_revision=candidate_revision",
        "真实 `export` check",
        'push_update(action="progress"',
        'push_update(action="fail"',
        'push_update(action="complete")',
        "`REVISION_CONFLICT`",
        "新 attempt 会返回新的独立 `work_path`",
        "用户明确结束协作时调用 `close_session`",
        "页面和 daemon 可以继续驻留",
        "桥不可用",
        "直接走下方原工作流",
    ]
    missing = [fragment for fragment in required if fragment not in text]
    check(not missing, "SKILL bridge contract missing: " + " | ".join(missing))
    section = text.split("### 可选：编辑器↔Agent 桥协作", 1)[1].split("### Step 0 · 明确输入", 1)[0]
    check(section.count("--force --track both") >= 2, "bridge convert command is not fixed to complete both tracks")
    check(all(name in section for name in ('"render"', '"capacity"', '"images"', '"manifest"')), "generation validation check names incomplete")


async def integration_group():
    skill_contract_check()
    with tempfile.TemporaryDirectory(prefix="bridge-integration-") as tmp:
        root = Path(tmp)
        try:
            async with MCPClient(tmp) as client:
                opened_call = await client.session.call_tool("open_editor", {
                    "deck_path": None, "output_path": "index.html", "view": "brief", "open_browser": False})
                check(not opened_call.isError, opened_call.content)
                opened = opened_call.structuredContent
                check(opened["phase"] == "briefing" and opened["revision"] is None and not (root / "index.html").exists(), "no-deck open created a fake target")

                fragment = extract_fragment(opened["url"])
                browser_token = fragment["brt"][0]
                client_id = str(uuid.uuid4())
                heartbeat = {
                    "protocol_version": 2, "role": "browser", "session_id": opened["session_id"],
                    "client_id": client_id, "dirty": False, "active_edit": False,
                    "draft_pending": False, "revision": None, "last_event_id": 0,
                }
                code, bound = one_request(opened["url"].split("/editor.html", 1)[0], "/api/bridge/heartbeat", heartbeat, browser_token, opened["url"].split("/editor.html", 1)[0])
                check(code == 200 and bound["client_id"] == client_id, bound)

                intent_id = str(uuid.uuid4())
                intent = {
                    "protocol_version": 2, "intent_id": intent_id, "session_id": opened["session_id"],
                    "type": "brief.submitted", "base_revision": None,
                    "payload": {"text": "确定性桥集成简报", "json": {"kind": "design-brief", "topic": "bridge"}},
                    "client_ts": "2026-10-03T00:00:00Z",
                }
                origin = opened["url"].split("/editor.html", 1)[0]
                code, accepted = one_request(origin, "/api/intent", intent, browser_token, origin)
                check(code == 200 and accepted["accepted"], accepted)

                discovery = json.loads((root / ".pptx-html" / "serve.json").read_text())
                management = discovery["management_token"]
                driver_consumer = str(uuid.uuid4())
                driver_open = managed_post(origin, management, "/api/bridge/open", {
                    "consumer_id": driver_consumer, "deck_path": None, "output_path": "index.html",
                    "view": "brief", "open_browser": False})
                check(driver_open["session_id"] == opened["session_id"], "HTTP driver did not reuse MCP-opened session")
                claimed = managed_post(origin, management, "/api/bridge/await", {
                    "session_id": opened["session_id"], "consumer_id": driver_consumer, "timeout_sec": 1})
                check(claimed["kind"] == "intent" and claimed["intent_id"] == intent_id and claimed["attempt"] == 1, claimed)
                work_path = Path(claimed["work_path"])
                check(work_path != Path(claimed["target_path"]) and not Path(claimed["target_path"]).exists(), "attempt was not isolated from target")
                work_path.parent.mkdir(parents=True, exist_ok=True)
                work_path.write_text(minimal_deck("确定性桥发布"), encoding="utf-8")

                progress = managed_post(origin, management, "/api/bridge/update", {
                    "session_id": opened["session_id"], "intent_id": intent_id, "attempt": 1,
                    "consumer_id": driver_consumer, "action": "progress",
                    "message": "deterministic validation", "validation": None})
                check(progress["status"] == "processing", progress)

                checks = []
                for name in ("manifest", "render", "capacity", "images"):
                    argv = [sys.executable, "-c", "from pathlib import Path; import sys; p=Path(sys.argv[1]); assert p.is_file() and 'data-slide-id' in p.read_text(encoding='utf-8')", str(work_path)]
                    run = subprocess.run(argv, capture_output=True, text=True)
                    check(run.returncode == 0, f"deterministic {name} command failed: {run.stderr}")
                    checks.append({"name": name, "argv": argv, "exit_code": run.returncode, "report_path": None})

                revision_argv = [sys.executable, str(ROOT / "tools" / "bridge_core.py"), "revision", str(work_path)]
                revision_run = subprocess.run(revision_argv, cwd=ROOT, capture_output=True, text=True)
                candidate = revision_run.stdout.strip()
                check(revision_run.returncode == 0 and candidate.startswith("sha256:") and len(candidate) == 71 and all(c in "0123456789abcdef" for c in candidate[7:]), f"revision CLI failed: {revision_run.stderr or candidate}")

                complete_args = {
                    "session_id": opened["session_id"], "intent_id": intent_id, "attempt": 1,
                    "consumer_id": driver_consumer, "action": "complete",
                    "message": "deterministic bridge integration complete",
                    "validation": {"candidate_revision": candidate, "checks": checks},
                }
                completed = managed_post(origin, management, "/api/bridge/update", complete_args)
                check(completed["status"] == "succeeded" and completed["revision"] == candidate, completed)
                check((root / "index.html").read_text(encoding="utf-8") == work_path.read_text(encoding="utf-8"), "published target differs from validated work_path")

                replay = managed_post(origin, management, "/api/bridge/update", complete_args)
                check(replay["receipt_id"] == completed["receipt_id"], "complete replay did not return original receipt")
                for _ in range(2):
                    timeout = managed_post(origin, management, "/api/bridge/await", {
                        "session_id": opened["session_id"], "consumer_id": driver_consumer, "timeout_sec": 1})
                    check(timeout["kind"] == "timeout", "bounded reattach did not return timeout")
                status_call = await client.session.call_tool("get_status", {"session_id": opened["session_id"]})
                check(not status_call.isError and status_call.structuredContent["revision"] == candidate, status_call.content)
                driver_closed = managed_post(origin, management, "/api/bridge/close", {
                    "session_id": opened["session_id"], "consumer_id": driver_consumer, "reason": "integration-complete"})
                check(driver_closed["consumer_state"] == "paused", driver_closed)

                second_id = str(uuid.uuid4())
                second_intent = {
                    "protocol_version": 2, "intent_id": second_id, "session_id": opened["session_id"],
                    "type": "brief.submitted", "base_revision": candidate,
                    "payload": {"text": "MCP complete 回归", "json": {"kind": "design-brief", "topic": "mcp-complete"}},
                    "client_ts": "2026-10-03T00:00:01Z",
                }
                code, second_accepted = one_request(origin, "/api/intent", second_intent, browser_token, origin)
                check(code == 200 and second_accepted["accepted"], second_accepted)
                mcp_claim = await client.session.call_tool("await_intent", {"session_id": opened["session_id"], "timeout_sec": 1})
                check(not mcp_claim.isError and mcp_claim.structuredContent["intent_id"] == second_id, mcp_claim.content)
                mcp_work = Path(mcp_claim.structuredContent["work_path"])
                mcp_work.write_text(minimal_deck("MCP complete 发布"), encoding="utf-8")
                mcp_revision_run = subprocess.run(
                    [sys.executable, str(ROOT / "tools" / "bridge_core.py"), "revision", str(mcp_work)],
                    cwd=ROOT, capture_output=True, text=True)
                mcp_candidate = mcp_revision_run.stdout.strip()
                mcp_checks = [{"name": name, "argv": ["deterministic-check", name], "exit_code": 0, "report_path": None}
                              for name in ("manifest", "render", "capacity", "images")]
                mcp_complete = await client.session.call_tool("push_update", {
                    "session_id": opened["session_id"], "intent_id": second_id, "attempt": 1,
                    "action": "complete", "message": "MCP complete regression",
                    "validation": {"candidate_revision": mcp_candidate, "checks": mcp_checks},
                })
                check(not mcp_complete.isError and mcp_complete.structuredContent["status"] == "succeeded", mcp_complete.content)
                check((root / "index.html").read_text(encoding="utf-8") == mcp_work.read_text(encoding="utf-8"), "MCP complete did not publish its validated work_path")

                closed_call = await client.session.call_tool("close_session", {"session_id": opened["session_id"], "reason": "integration-complete"})
                check(not closed_call.isError and closed_call.structuredContent["consumer_state"] == "paused", closed_call.content)
        finally:
            discovery_path = root / ".pptx-html" / "serve.json"
            if discovery_path.exists():
                discovery = json.loads(discovery_path.read_text())
                with contextlib.suppress(Exception):
                    one_request(discovery["origin"], "/api/bridge/stop", {"reason": "cli-stop"}, discovery["management_token"])
    print("PASS integration: SKILL bridge contract + real MCP/HTTP no-deck claim, isolated work_path, revision CLI, validation publish, receipt replay, bounded reattach")


RESULT_DIR = ROOT / "tests" / "harness" / "results" / "bridge"


def write_group_report(name, result):
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULT_DIR / "report.json"
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        report = {"schema_version": 1, "groups": {}}
    report["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report.setdefault("groups", {})[name] = result
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class CapturingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed = []

    def addSuccess(self, test):
        self.passed.append(test.id())
        super().addSuccess(test)


def fault_sse_resync_case():
    with tempfile.TemporaryDirectory(prefix="bridge-fault-sse-") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text(minimal_deck("SSE resync"), encoding="utf-8")
        with live_daemon(root) as (core, origin, management):
            opened = managed_post(origin, management, "/api/bridge/open", {
                "consumer_id": "fault-sse-consumer", "deck_path": str(root / "index.html"),
                "output_path": "index.html", "view": "edit", "open_browser": False})
            token = extract_fragment(opened["url"])["brt"][0]
            client_id = str(uuid.uuid4())
            heartbeat = {"protocol_version": 2, "role": "browser", "session_id": opened["session_id"],
                         "client_id": client_id, "dirty": False, "active_edit": False,
                         "draft_pending": False, "revision": opened["revision"], "last_event_id": 0}
            code, _ = one_request(origin, "/api/bridge/heartbeat", heartbeat, token, origin)
            check(code == 200, "fault SSE browser bind failed")
            with core.db:
                expired = core._event(opened["session_id"], "notice", {
                    "session_id": opened["session_id"], "intent_id": "expired", "level": "info", "message": "old"})
                latest = core._event(opened["session_id"], "notice", {
                    "session_id": opened["session_id"], "intent_id": "latest", "level": "info", "message": "new"})
                core.db.execute("DELETE FROM events WHERE id=?", (expired,))
            parsed = urlsplit(origin)
            conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
            conn.request("GET", f"/api/events?session_id={opened['session_id']}&after={expired}", headers={
                "Authorization": "Bearer " + token, "Sec-Fetch-Site": "same-origin"})
            response = conn.getresponse()
            lines = []
            while len(lines) < 8:
                line = response.readline().decode("utf-8")
                if not line:
                    break
                lines.append(line)
                if line == "\n":
                    break
            conn.close()
            check(response.status == 200, f"fault SSE status {response.status}")
            check(f"id: {latest}\n" in lines and "event: resync-required\n" in lines,
                  f"expired cursor did not emit resync-required: {lines}")
            data_line = next((line for line in lines if line.startswith("data: ")), None)
            data = json.loads(data_line[6:]) if data_line else {}
            check(data == {"latest_event_id": latest, "revision": opened["revision"],
                           "session_id": opened["session_id"]}, f"resync payload mismatch: {data}")
    return {"status": "PASS", "expired_cursor": expired, "latest_event_id": latest}


def fault_group():
    from tests.harness import test_bridge_core
    names = [
        "CoreCase.test_response_loss_intent_claim_open_close_and_retry",
        "CoreCase.test_complete_response_loss_replays_after_restart_without_republish",
        "CoreCase.test_two_consumers_and_two_daemon_lock_are_exclusive",
        "CoreCase.test_a_class_save_asset_rollback_response_loss_receipts",
        "CoreCase.test_external_side_effect_is_not_automatically_replayed",
        "PublicationRecoveryCase.test_prepared_applying_each_file_and_git_ref_recover_old",
        "PublicationRecoveryCase.test_db_committed_repairs_old_target_without_duplicate_receipt_or_events",
        "PublicationRecoveryCase.test_third_party_bytes_freeze_recovery",
        "SecurityAndMigrationCase.test_schema_v2_migrates_and_future_schema_is_rejected",
    ]
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for name in names:
        suite.addTests(loader.loadTestsFromName(name, test_bridge_core))
    stream = io.StringIO()
    started = time.monotonic()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=CapturingResult).run(suite)
    unittest_record = {
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun,
        "passed": result.passed,
        "failures": [{"test": test.id(), "traceback": trace} for test, trace in result.failures],
        "errors": [{"test": test.id(), "traceback": trace} for test, trace in result.errors],
        "duration_sec": round(time.monotonic() - started, 6),
        "captured_output": stream.getvalue(),
    }
    sse_record = None
    sse_error = None
    try:
        sse_record = fault_sse_resync_case()
    except Exception as exc:
        sse_error = f"{type(exc).__name__}: {exc}"
    passed = result.wasSuccessful() and sse_error is None
    report = {
        "status": "PASS" if passed else "FAIL",
        "coverage": ["FAULT-01 publication injector matrix", "FAULT-02 complete response loss",
                     "FAULT-03 intent/claim/open/close/retry response loss", "FAULT-04 A-class receipts",
                     "FAULT-05 external side-effect boundary", "double consumer", "double daemon lock",
                     "SSE-06 expired cursor resync", "CNS-04 third-party bytes", "schema migration"],
        "unittest": unittest_record,
        "sse_resync": sse_record or {"status": "FAIL", "error": sse_error},
        "limitations": ["SIGKILL simulates process loss, not hardware power-loss durability",
                        "browser DOM retention on draft transport failure remains covered by the UI group, not this core fault group"],
    }
    write_group_report("fault", report)
    check(passed, "fault group failed; see tests/harness/results/bridge/report.json")
    print(f"PASS fault: {result.testsRun} captured unittest cases + real HTTP SSE expired-cursor resync")


def percentile(samples, fraction):
    ordered = sorted(samples)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def distribution(samples):
    return {"count": len(samples), "p50_ms": round(percentile(samples, .50), 3),
            "p95_ms": round(percentile(samples, .95), 3), "max_ms": round(max(samples), 3),
            "samples_ms": [round(value, 3) for value in samples]}


def process_resources(pid):
    values = {"rss_mib": None, "fd_count": None}
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                values["rss_mib"] = round(int(line.split()[1]) / 1024, 3)
                break
        values["fd_count"] = len(list(Path(f"/proc/{pid}/fd").iterdir()))
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        pass
    return values


def command_version(argv):
    try:
        run = subprocess.run(argv, capture_output=True, text=True, timeout=10)
        return (run.stdout or run.stderr).splitlines()[0].strip() if run.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, IndexError):
        return None


def performance_environment(root):
    chromium = next((shutil.which(name) for name in ("chromium", "chromium-browser", "google-chrome") if shutil.which(name)), None)
    memory = {}
    with contextlib.suppress(OSError):
        memory = {line.split(":", 1)[0]: line.split(":", 1)[1].strip()
                  for line in Path("/proc/meminfo").read_text().splitlines()
                  if line.startswith(("MemTotal:", "MemAvailable:"))}
    usage = shutil.disk_usage(root)
    try:
        sdk_version = importlib.metadata.version("mcp")
    except importlib.metadata.PackageNotFoundError:
        sdk_version = None
    return {
        "platform": platform.platform(), "python": sys.version.splitlines()[0],
        "mcp_sdk": sdk_version, "git": command_version(["git", "--version"]),
        "chromium": command_version([chromium, "--version"]) if chromium else None,
        "cpu_count": os.cpu_count(), "load_average": list(os.getloadavg()), "memory": memory,
        "disk": {"total_gib": round(usage.total / 1024 ** 3, 3),
                 "free_gib": round(usage.free / 1024 ** 3, 3)},
    }


def performance_group():
    with tempfile.TemporaryDirectory(prefix="bridge-performance-") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text(minimal_deck("Performance small deck"), encoding="utf-8")
        proc = subprocess.Popen([sys.executable, str(EDIT), tmp, "--daemon", "--port", "0"], cwd=ROOT,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            discovery_path = root / ".pptx-html" / "serve.json"
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and not discovery_path.exists():
                time.sleep(.05)
            check(discovery_path.exists(), "performance daemon did not publish discovery")
            discovery = json.loads(discovery_path.read_text())
            origin, management = discovery["origin"], discovery["management_token"]
            opened = []
            for consumer in ("perf-a", "perf-b"):
                code, item = one_request(origin, "/api/bridge/open", {
                    "consumer_id": consumer, "deck_path": str(root / "index.html"),
                    "output_path": "index.html", "view": "edit", "open_browser": False}, management)
                check(code == 200, item)
                opened.append(item)
            sid = opened[0]["session_id"]
            tabs = []
            for item in opened:
                token = extract_fragment(item["url"])["brt"][0]
                client = str(uuid.uuid4())
                body = {"protocol_version": 2, "role": "browser", "session_id": sid,
                        "client_id": client, "dirty": False, "active_edit": False,
                        "draft_pending": False, "revision": item["revision"], "last_event_id": 0}
                code, response = one_request(origin, "/api/bridge/heartbeat", body, token, origin)
                check(code == 200, response)
                tabs.append((token, body))

            resources = {"baseline": process_resources(proc.pid)}
            for index in range(20):
                code, status = one_request(origin, "/api/bridge/status", {"session_id": sid}, management)
                check(code == 200 and status["session_id"] == sid, status)
                token, heartbeat = tabs[index % 2]
                code, response = one_request(origin, "/api/bridge/heartbeat", heartbeat, token, origin)
                check(code == 200, response)

            long_results = {}
            def long_poll(label, timeout_sec):
                started = time.monotonic()
                code, response = one_request(origin, "/api/bridge/await", {
                    "session_id": sid, "consumer_id": "perf-a", "timeout_sec": timeout_sec},
                    management, timeout=timeout_sec + 10)
                elapsed = (time.monotonic() - started) * 1000
                long_results[label] = {"requested_sec": timeout_sec, "elapsed_ms": round(elapsed, 3),
                                       "http_status": code, "kind": response.get("kind")}

            await_25 = threading.Thread(target=long_poll, args=("await_25s", 25), daemon=True)
            await_25.start()
            time.sleep(.1)
            status_samples = []
            for _ in range(100):
                started = time.monotonic()
                code, status = one_request(origin, "/api/bridge/status", {"session_id": sid}, management)
                status_samples.append((time.monotonic() - started) * 1000)
                check(code == 200 and status["session_id"] == sid, status)
            heartbeat_samples = []
            for index in range(100):
                token, heartbeat = tabs[index % 2]
                started = time.monotonic()
                code, response = one_request(origin, "/api/bridge/heartbeat", heartbeat, token, origin)
                heartbeat_samples.append((time.monotonic() - started) * 1000)
                check(code == 200, response)
            await_25.join(timeout=32)
            check(not await_25.is_alive(), "25 second await did not terminate")
            resources["after_status_heartbeat"] = process_resources(proc.pid)

            long_poll("await_120s", 120)
            resources["after_longpoll"] = process_resources(proc.pid)

            def intent_body(text):
                return {"protocol_version": 2, "intent_id": str(uuid.uuid4()), "session_id": sid,
                        "type": "brief.submitted", "base_revision": opened[0]["revision"],
                        "payload": {"text": text, "json": {"kind": "design-brief", "topic": "性能"}},
                        "client_ts": "2026-10-03T00:00:00Z"}

            token = tabs[0][0]
            for _ in range(20):
                code, accepted = one_request(origin, "/api/intent", intent_body("中文预热" * 64), token, origin)
                check(code == 200 and accepted["accepted"], accepted)
            intent_samples = []
            for _ in range(200):
                started = time.monotonic()
                code, accepted = one_request(origin, "/api/intent", intent_body("中文小载荷" * 128), token, origin)
                intent_samples.append((time.monotonic() - started) * 1000)
                check(code == 200 and accepted["accepted"], accepted)
            near_limit_samples = []
            near_limit_text = "近上限中文" * 60000
            for _ in range(20):
                started = time.monotonic()
                code, accepted = one_request(origin, "/api/intent", intent_body(near_limit_text), token, origin, timeout=10)
                near_limit_samples.append((time.monotonic() - started) * 1000)
                check(code == 200 and accepted["accepted"], accepted)
            resources["final"] = process_resources(proc.pid)
            rss_samples = [sample["rss_mib"] for sample in resources.values() if sample["rss_mib"] is not None]
            fd_samples = [sample["fd_count"] for sample in resources.values() if sample["fd_count"] is not None]
            resources["summary"] = {
                "rss_baseline_mib": resources["baseline"]["rss_mib"],
                "rss_peak_mib": max(rss_samples) if rss_samples else None,
                "rss_final_mib": resources["final"]["rss_mib"],
                "rss_growth_mib": round(resources["final"]["rss_mib"] - resources["baseline"]["rss_mib"], 3)
                    if resources["final"]["rss_mib"] is not None and resources["baseline"]["rss_mib"] is not None else None,
                "fd_baseline": resources["baseline"]["fd_count"],
                "fd_peak": max(fd_samples) if fd_samples else None,
                "fd_final": resources["final"]["fd_count"],
                "fd_growth": resources["final"]["fd_count"] - resources["baseline"]["fd_count"]
                    if resources["final"]["fd_count"] is not None and resources["baseline"]["fd_count"] is not None else None,
            }
            for sample in long_results.values():
                sample.update({"count": 1, "p50_ms": sample["elapsed_ms"],
                               "p95_ms": sample["elapsed_ms"], "max_ms": sample["elapsed_ms"]})

            metrics = {
                "schema_version": 1,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "fixture": {"kind": "temporary-small-deck", "slides": 1, "bytes": (root / "index.html").stat().st_size},
                "environment": performance_environment(root),
                "protocol": {
                    "status": distribution(status_samples), "heartbeat": distribution(heartbeat_samples),
                    "intent_small": distribution(intent_samples), "intent_near_1mib": distribution(near_limit_samples),
                    "longpoll": long_results,
                },
                "resources": resources,
            }
            checks = {
                "PERF-01 status p95 <=250ms": metrics["protocol"]["status"]["p95_ms"] <= 250,
                "PERF-01 heartbeat p95 <=250ms": metrics["protocol"]["heartbeat"]["p95_ms"] <= 250,
                "PERF-02 small intent p95 <=500ms": metrics["protocol"]["intent_small"]["p95_ms"] <= 500,
                "PERF-02 near-limit intent p95 <=2000ms": metrics["protocol"]["intent_near_1mib"]["p95_ms"] <= 2000,
                "PERF-04 25s timeout <= timeout+5s": long_results["await_25s"]["kind"] == "timeout" and long_results["await_25s"]["elapsed_ms"] <= 30000,
                "PERF-04 120s timeout <= timeout+5s": long_results["await_120s"]["kind"] == "timeout" and long_results["await_120s"]["elapsed_ms"] <= 125000,
            }
            metrics["thresholds"] = checks
            RESULT_DIR.mkdir(parents=True, exist_ok=True)
            (RESULT_DIR / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            blocked = [
                {"id": "PERF-03", "reason": "bake-mix/cmb-retail real deck fixtures are unavailable; event-to-editable UI scale remains external"},
                {"id": "PERF-04-full-sample", "reason": "explicit bounded run uses one 25s and one 120s sample, not acceptance-plan 20/3 samples"},
                {"id": "PERF-05", "reason": "20 independent cold-start distribution not part of this bounded protocol run"},
                {"id": "PERF-06-30min", "reason": "30-minute idle and full 100 connect/disconnect stability remain external"},
                {"id": "CNS-08", "reason": "54-page 10x asset load unavailable"},
            ]
            report = {"status": "PASS" if all(checks.values()) else "FAIL", "thresholds": checks,
                      "metrics_path": "tests/harness/results/bridge/metrics.json", "blocked": blocked,
                      "scope": "temporary one-slide protocol benchmark; not a real-deck scale certification"}
            write_group_report("performance", report)
            check(all(checks.values()), "performance threshold failure; see metrics.json")
            print("PASS performance: status p95={:.3f}ms heartbeat p95={:.3f}ms intent p95={:.3f}ms near-limit p95={:.3f}ms; await={:.3f}s/{:.3f}s".format(
                metrics["protocol"]["status"]["p95_ms"], metrics["protocol"]["heartbeat"]["p95_ms"],
                metrics["protocol"]["intent_small"]["p95_ms"], metrics["protocol"]["intent_near_1mib"]["p95_ms"],
                long_results["await_25s"]["elapsed_ms"] / 1000, long_results["await_120s"]["elapsed_ms"] / 1000))
        finally:
            if proc.poll() is None:
                with contextlib.suppress(Exception):
                    discovery = json.loads((root / ".pptx-html" / "serve.json").read_text())
                    one_request(discovery["origin"], "/api/bridge/stop", {"reason": "cli-stop"}, discovery["management_token"])
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.terminate(); proc.wait(timeout=5)


async def main_async(groups):
    if "transport" in groups: await transport_group()
    if "sdk" in groups: await sdk_group()
    if "http" in groups or "security" in groups: await asyncio.to_thread(http_group)
    if "ui" in groups: await asyncio.to_thread(ui_group)
    if "integration" in groups: await integration_group()
    if "fault" in groups: await asyncio.to_thread(fault_group)
    if "performance" in groups: await asyncio.to_thread(performance_group)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", choices=["transport","sdk","http","ui","fault","security","integration","performance"], action="append")
    ap.add_argument("--probe-server", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.probe_server:
        asyncio.run(probe_server()); return
    groups = set(args.group or ["transport","sdk","http","ui","fault","integration"])
    asyncio.run(main_async(groups))
    print("PASS r_bridge_check selected automatic groups: " + ",".join(sorted(groups)))


if __name__ == "__main__":
    main()
