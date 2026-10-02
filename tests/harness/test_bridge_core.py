#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from bridge_core import (  # noqa: E402
    ASSET_RAW_MAX, BOOTSTRAP_TTL_SEC, BridgeCore, BridgeError,
    CLIENT_ONLINE_SEC, CONSUMER_LEASE_SEC, CONTROL_BODY_MAX,
    DOCUMENT_BODY_MAX, INTENT_INLINE_MAX, INTENT_PAYLOAD_MAX,
    PROTOCOL_VERSION, revision_cli,
)


def golden_revision(root: Path, names):
    records = []
    for name in sorted(names, key=lambda x: x.encode("utf-8")):
        raw = (root / name).read_bytes()
        records.append([name, len(raw), hashlib.sha256(raw).hexdigest()])
    encoded = json.dumps(records, ensure_ascii=False, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(b"pptx-html-source-v1\n" + encoded).hexdigest()


class CoreCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bridge-core-")
        self.root = Path(self.tmp.name)
        self.core = BridgeCore(self.root)
        self.core.origin = "http://127.0.0.1:9999"

    def tearDown(self):
        self.core.close()
        self.tmp.cleanup()

    def make_deck(self):
        (self.root / "assets").mkdir(exist_ok=True)
        (self.root / "fonts").mkdir(exist_ok=True)
        (self.root / "index.html").write_bytes(b"<!doctype html><title>A</title>")
        (self.root / "assets" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\nA")
        (self.root / "fonts" / "a.woff2").write_bytes(b"font")

    def open(self, consumer="consumer-a"):
        self.make_deck()
        return self.core.open_editor(consumer, str(self.root / "index.html"), open_browser=False)

    def submit(self, opened, intent_id=None, payload=None):
        intent_id = intent_id or str(uuid.uuid4())
        payload = payload or {"formats": ["pptx"], "scope": "all"}
        return self.core.accept_intent(opened["session_id"], {
            "protocol_version": 2, "intent_id": intent_id,
            "session_id": opened["session_id"], "type": "convert.requested",
            "base_revision": opened["revision"], "payload": payload,
            "client_ts": "2026-10-02T00:00:00Z",
        })

    def test_constants_match_frozen_contract(self):
        self.assertEqual(PROTOCOL_VERSION, 2)
        self.assertEqual(CONTROL_BODY_MAX, 2 * 1024 * 1024)
        self.assertEqual(DOCUMENT_BODY_MAX, 64 * 1024 * 1024)
        self.assertEqual(INTENT_PAYLOAD_MAX, 1024 * 1024)
        self.assertEqual(INTENT_INLINE_MAX, 16 * 1024)
        self.assertEqual(ASSET_RAW_MAX, 32 * 1024 * 1024)
        self.assertEqual((CONSUMER_LEASE_SEC, CLIENT_ONLINE_SEC, BOOTSTRAP_TTL_SEC), (90, 45, 300))

    def test_schema_wal_and_required_tables(self):
        names = {r[0] for r in self.core.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for name in {"sessions", "consumers", "bootstrap_tokens", "intents", "attempts",
                     "retry_receipts", "write_receipts", "events", "clients", "bundle_files",
                     "snapshots", "publications"}:
            self.assertIn(name, names)
        self.assertEqual(self.core.db.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(self.core.db.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_source_revision_golden_raw_bytes(self):
        self.make_deck()
        session = self.core.register_session(deck_path=str(self.root / "index.html"))
        expected = golden_revision(self.root, ["assets/a.png", "fonts/a.woff2", "index.html"])
        self.assertEqual(session["revision"], expected)
        self.assertEqual(revision_cli(self.root / "index.html"), expected)
        (self.root / "assets" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\nB")
        self.assertNotEqual(self.core.observe_revision(session["id"]), expected)

    def test_open_registers_without_acquiring_and_close_requires_reopen(self):
        opened = self.open()
        self.assertEqual(opened["consumer_state"], "registered")
        self.assertEqual(opened["agent_state"], "offline")
        timeout = self.core.await_intent(opened["session_id"], "consumer-a", 1)
        self.assertEqual(timeout["kind"], "timeout")
        closed = self.core.close_consumer(opened["session_id"], "consumer-a")
        self.assertEqual(closed["consumer_state"], "paused")
        with self.assertRaises(BridgeError) as caught:
            self.core.await_intent(opened["session_id"], "consumer-a", 1)
        self.assertEqual(caught.exception.code, "RECOVERY_REQUIRED")
        reopened = self.core.open_editor("consumer-a", str(self.root / "index.html"), open_browser=False)
        self.assertEqual(reopened["session_id"], opened["session_id"])
        self.assertEqual(reopened["consumer_state"], "registered")

    def test_intent_uuid_idempotency_claim_redelivery_and_attempt_path(self):
        opened = self.open()
        iid = str(uuid.uuid4())
        first = self.submit(opened, iid)
        second = self.submit(opened, iid)
        self.assertEqual((first["seq"], first["status"]), (second["seq"], second["status"]))
        with self.assertRaises(BridgeError) as caught:
            self.submit(opened, iid, {"formats": ["pdf"], "scope": "all"})
        self.assertEqual(caught.exception.code, "IDEMPOTENCY_CONFLICT")
        claimed = self.core.await_intent(opened["session_id"], "consumer-a", 1)
        self.assertIn(f"jobs/{iid}/attempt-1/work/index.html", claimed["work_path"])
        Path(claimed["work_path"]).write_text("producer marker", encoding="utf-8")
        again = self.core.await_intent(opened["session_id"], "consumer-a", 1)
        self.assertTrue(again["redelivered"])
        self.assertEqual(Path(again["work_path"]).read_text(), "producer marker")

    def test_fail_retry_receipt_and_independent_attempt(self):
        opened = self.open()
        iid = str(uuid.uuid4())
        self.submit(opened, iid)
        claimed = self.core.await_intent(opened["session_id"], "consumer-a", 1)
        self.core.push_update(opened["session_id"], iid, 1, "consumer-a", "fail", "failed")
        retry_id = str(uuid.uuid4())
        body = {"session_id": opened["session_id"], "intent_id": iid,
                "retry_id": retry_id, "expected_attempt": 1, "mode": "rebuild",
                "base_revision": opened["revision"], "confirmed": True}
        one = self.core.retry_intent(opened["session_id"], body)
        two = self.core.retry_intent(opened["session_id"], body)
        self.assertEqual(one, two)
        self.assertEqual(one["attempt"], 2)
        next_claim = self.core.await_intent(opened["session_id"], "consumer-a", 1)
        self.assertIn("attempt-2", next_claim["work_path"])
        self.assertNotEqual(next_claim["work_path"], claimed["work_path"])
        self.assertTrue(Path(claimed["work_path"]).exists())

    def test_convert_claim_clears_inherited_export_and_records_baseline(self):
        self.make_deck();export=self.root/"export";native=export/"native";native.mkdir(parents=True)
        for rel,data in [("deck.pptx",b"old-editable"),("deck-vector.pptx",b"old-vector"),("deck.pdf",b"old-pdf"),("manifest.json",b"{}")]:
            (export/rel).write_bytes(data)
        (native/"page-01.png").write_bytes(b"old-native")
        opened=self.core.open_editor("consumer-a",str(self.root/"index.html"),open_browser=False);iid=str(uuid.uuid4());self.submit(opened,iid)
        claimed=self.core.await_intent(opened["session_id"],"consumer-a",1);work_export=Path(claimed["work_path"]).parent/"export"
        self.assertTrue(work_export.is_dir());self.assertEqual(list(work_export.iterdir()),[])
        baseline=json.loads(self.core.db.execute("SELECT export_baseline_json FROM attempts WHERE intent_id=?",(iid,)).fetchone()[0])
        self.assertGreaterEqual(len(baseline),5)

    def test_save_receipt_replay_cas_and_git_index_isolation(self):
        self.make_deck()
        subprocess.run(["git", "init"], cwd=self.root, check=True, capture_output=True)
        (self.root / "unrelated.txt").write_text("staged")
        subprocess.run(["git", "add", "unrelated.txt"], cwd=self.root, check=True)
        index = self.root / ".git" / "index"
        before = hashlib.sha256(index.read_bytes()).hexdigest()
        opened = self.core.open_editor("consumer-a", str(self.root / "index.html"), open_browser=False)
        html = "<!doctype html><title>saved</title>"
        r1 = self.core.save(opened["session_id"], "index.html", html, opened["revision"])
        r2 = self.core.save(opened["session_id"], "index.html", html, opened["revision"])
        self.assertEqual(r1["receipt_id"], r2["receipt_id"])
        self.assertEqual((self.root / "index.html").read_text(), html)
        self.assertEqual(hashlib.sha256(index.read_bytes()).hexdigest(), before)
        self.assertEqual(subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=self.root, capture_output=True).returncode, 128)
        self.assertEqual(self.core.db.execute("SELECT COUNT(*) FROM write_receipts").fetchone()[0], 1)

    def test_briefing_has_no_fake_html(self):
        opened = self.core.open_editor("consumer-a", None, "nested/new.html", open_browser=False)
        self.assertIsNone(opened["deck_path"])
        self.assertIsNone(opened["revision"])
        self.assertEqual(opened["phase"], "briefing")
        self.assertEqual(opened["resource_path"], "nested/new.html")
        self.assertFalse((self.root / "nested" / "new.html").exists())

    def test_complete_validation_publication_and_receipt_replay(self):
        opened = self.open()
        iid = str(uuid.uuid4())
        payload = {"text": "brief", "json": {"kind": "design-brief"}}
        accepted = self.core.accept_intent(opened["session_id"], {
            "protocol_version": 2, "intent_id": iid, "session_id": opened["session_id"],
            "type": "brief.submitted", "base_revision": opened["revision"],
            "payload": payload, "client_ts": "2026-10-02T00:00:00Z",
        })
        claimed = self.core.await_intent(opened["session_id"], "consumer-a", 1)
        work_path = Path(claimed["work_path"])
        work_path.write_text("<!doctype html><title>published</title>", encoding="utf-8")
        candidate = revision_cli(work_path)
        checks = [{"name": name, "argv": ["test", name], "exit_code": 0, "report_path": None}
                  for name in ("render", "capacity", "images", "manifest")]
        validation = {"candidate_revision": candidate, "checks": checks}
        first = self.core.push_update(opened["session_id"], iid, 1, "consumer-a", "complete", "done", validation)
        event_count = self.core.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        second = self.core.push_update(opened["session_id"], iid, 1, "consumer-a", "complete", "ignored", {"bad": True})
        self.assertEqual(first["receipt_id"], second["receipt_id"])
        self.assertEqual(self.core.db.execute("SELECT COUNT(*) FROM events").fetchone()[0], event_count)
        self.assertIn("published", (self.root / "index.html").read_text())
        self.assertEqual(self.core.db.execute("SELECT status FROM publications ORDER BY created_at DESC LIMIT 1").fetchone()[0], "COMMITTED")
        self.assertEqual(self.core.db.execute("SELECT status FROM intents WHERE id=?", (iid,)).fetchone()[0], "succeeded")

    def test_response_loss_intent_claim_open_close_and_retry(self):
        opened = self.open()
        sid = opened["session_id"]
        iid = str(uuid.uuid4())
        accepted = self.submit(opened, iid)
        accepted_replay = self.submit(opened, iid)
        self.assertEqual(accepted, accepted_replay)
        claimed = self.core.await_intent(sid, "consumer-a", 1)
        claim_replay = self.core.await_intent(sid, "consumer-a", 1)
        self.assertTrue(claim_replay["redelivered"])
        self.assertEqual((claimed["intent_id"], claimed["attempt"], claimed["work_path"]),
                         (claim_replay["intent_id"], claim_replay["attempt"], claim_replay["work_path"]))
        self.core.push_update(sid, iid, 1, "consumer-a", "fail", "deterministic failure")
        retry_id = str(uuid.uuid4())
        retry = {"session_id": sid, "intent_id": iid, "retry_id": retry_id,
                 "expected_attempt": 1, "mode": "rebuild", "base_revision": opened["revision"],
                 "confirmed": True}
        retry_result = self.core.retry_intent(sid, retry)
        self.assertEqual(retry_result, self.core.retry_intent(sid, retry))
        self.core.close()
        self.core = BridgeCore(self.root)
        self.core.origin = "http://127.0.0.1:9999"
        self.assertEqual(retry_result, self.core.retry_intent(sid, retry))
        reopened = self.core.open_editor("consumer-a", str(self.root / "index.html"), open_browser=False)
        self.assertEqual(reopened["session_id"], sid)
        close_one = self.core.close_consumer(sid, "consumer-a")
        close_two = self.core.close_consumer(sid, "consumer-a")
        self.assertEqual(close_one, close_two)
        self.assertEqual(self.core.db.execute("SELECT COUNT(*) FROM retry_receipts WHERE retry_id=?", (retry_id,)).fetchone()[0], 1)

    def test_complete_response_loss_replays_after_restart_without_republish(self):
        opened = self.open()
        sid = opened["session_id"]
        iid = str(uuid.uuid4())
        self.core.accept_intent(sid, {
            "protocol_version": 2, "intent_id": iid, "session_id": sid,
            "type": "brief.submitted", "base_revision": opened["revision"],
            "payload": {"text": "response loss", "json": {"kind": "design-brief"}},
            "client_ts": "2026-10-03T00:00:00Z",
        })
        claimed = self.core.await_intent(sid, "consumer-a", 1)
        work_path = Path(claimed["work_path"])
        work_path.write_text("<!doctype html><title>response-loss-complete</title>", encoding="utf-8")
        candidate = revision_cli(work_path)
        validation = {"candidate_revision": candidate, "checks": [
            {"name": name, "argv": ["test", name], "exit_code": 0, "report_path": None}
            for name in ("render", "capacity", "images", "manifest")]}
        complete_args = (sid, iid, 1, "consumer-a", "complete", "persisted before lost response", validation)
        first = self.core.push_update(*complete_args)
        counts = tuple(self.core.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                       for table in ("publications", "events", "snapshots", "facts"))
        self.core.close()
        self.core = BridgeCore(self.root)
        replay = self.core.push_update(*complete_args)
        self.assertEqual((replay["receipt_id"], replay["revision"], replay["events"]),
                         (first["receipt_id"], first["revision"], first["events"]))
        self.assertEqual(tuple(self.core.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                               for table in ("publications", "events", "snapshots", "facts")), counts)
        self.assertEqual(self.core.get_status(sid)["revision"], candidate)

    def test_two_consumers_and_two_daemon_lock_are_exclusive(self):
        opened = self.open()
        sid = opened["session_id"]
        self.core.open_editor("consumer-b", str(self.root / "index.html"), open_browser=False)
        self.core.await_intent(sid, "consumer-a", 1)
        with self.assertRaises(BridgeError) as busy:
            self.core.await_intent(sid, "consumer-b", 1)
        self.assertEqual(busy.exception.code, "SESSION_BUSY")
        with tempfile.TemporaryDirectory(prefix="bridge-lock-") as tmp:
            first = BridgeCore(tmp, require_lock=True)
            try:
                with self.assertRaises(BridgeError) as locked:
                    BridgeCore(tmp, require_lock=True)
                self.assertEqual(locked.exception.code, "SESSION_BUSY")
            finally:
                first.close()

    def test_a_class_save_asset_rollback_response_loss_receipts(self):
        opened = self.open()
        sid = opened["session_id"]
        baseline = next(v for v in self.core.versions(sid)["versions"] if v["message"] == "baseline")
        save_args = (sid, "index.html", "<!doctype html><title>saved-loss</title>", opened["revision"])
        saved = self.core.save(*save_args)
        save_counts = tuple(self.core.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                            for table in ("write_receipts", "publications", "events"))
        self.assertEqual(self.core.save(*save_args)["receipt_id"], saved["receipt_id"])
        self.assertEqual(tuple(self.core.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                               for table in ("write_receipts", "publications", "events")), save_counts)
        raw = b"\x89PNG\r\n\x1a\nresponse-loss"
        encoded = __import__("base64").b64encode(raw).decode()
        asset_args = (sid, "assets/lost.png", encoded, saved["revision"])
        asset = self.core.asset(*asset_args)
        asset_counts = tuple(self.core.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                             for table in ("write_receipts", "publications", "events"))
        self.assertEqual(self.core.asset(*asset_args)["receipt_id"], asset["receipt_id"])
        self.assertEqual(tuple(self.core.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                               for table in ("write_receipts", "publications", "events")), asset_counts)
        rollback_args = (sid, "index.html", baseline["snapshot_id"], asset["revision"])
        rolled = self.core.rollback(*rollback_args)
        rollback_counts = tuple(self.core.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                                for table in ("write_receipts", "publications", "events"))
        self.assertEqual(self.core.rollback(*rollback_args)["receipt_id"], rolled["receipt_id"])
        self.assertEqual(tuple(self.core.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                               for table in ("write_receipts", "publications", "events")), rollback_counts)
        with self.assertRaises(BridgeError) as stale:
            self.core.save(*save_args)
        self.assertEqual(stale.exception.code, "REVISION_CONFLICT")
        self.assertEqual(stale.exception.details["receipt_id"], saved["receipt_id"])

    def test_external_side_effect_is_not_automatically_replayed(self):
        opened = self.open()
        iid = str(uuid.uuid4())
        self.submit(opened, iid)
        claimed = self.core.await_intent(opened["session_id"], "consumer-a", 1)
        paid_calls = [claimed["intent_id"]]
        self.core.close()
        self.core = BridgeCore(self.root)
        self.assertEqual(paid_calls, [iid])
        self.assertEqual(self.core.db.execute("SELECT status FROM intents WHERE id=?", (iid,)).fetchone()[0], "interrupted")
        self.assertEqual(self.core.db.execute("SELECT COUNT(*) FROM attempts WHERE intent_id=?", (iid,)).fetchone()[0], 1)


class InjectedCrash(BaseException):
    pass


class PublicationRecoveryCase(unittest.TestCase):
    def _prepare(self, root, point, index=None):
        (root / "assets").mkdir();(root / "index.html").write_text("<html>old</html>");(root / "assets/a.png").write_bytes(b"\x89PNG\r\n\x1a\nold")
        def inject(actual, context):
            if actual == point and (index is None or context.get("index") == index):
                raise InjectedCrash(actual)
        core=BridgeCore(root,fault_injector=inject);core.origin="http://127.0.0.1:9"
        opened=core.open_editor("consumer",str(root/"index.html"),open_browser=False)
        return core,opened

    def _crash_save(self,root,point,index=None):
        core,opened=self._prepare(root,point,index)
        with self.assertRaises(InjectedCrash):core.save(opened["session_id"],"index.html","<html>new</html>",opened["revision"])
        core.close();return opened

    def test_prepared_applying_each_file_and_git_ref_recover_old(self):
        for repeat in range(3):
            for point,index in [("publication.prepared",None),("publication.applying",None),("publication.file_applied",0),("publication.file_applied",1),("publication.git_ref_updated",None)]:
                with self.subTest(repeat=repeat,point=point,index=index),tempfile.TemporaryDirectory(prefix="bridge-fault-") as tmp:
                    root=Path(tmp);opened=self._crash_save(root,point,index);recovered=BridgeCore(root)
                    try:
                        self.assertEqual((root/"index.html").read_text(),"<html>old</html>")
                        self.assertEqual((root/"assets/a.png").read_bytes(),b"\x89PNG\r\n\x1a\nold")
                        self.assertEqual(recovered.db.execute("SELECT status FROM publications ORDER BY created_at DESC LIMIT 1").fetchone()[0],"ROLLED_BACK")
                        self.assertEqual(recovered.db.execute("SELECT COUNT(*) FROM write_receipts").fetchone()[0],0)
                    finally:recovered.close()

    def test_db_committed_repairs_old_target_without_duplicate_receipt_or_events(self):
        for point in ("publication.db_committed", "publication.before_response"):
            with self.subTest(point=point), tempfile.TemporaryDirectory(prefix="bridge-commit-") as tmp:
                root=Path(tmp);opened=self._crash_save(root,point)
                if point == "publication.db_committed":
                    (root/"index.html").write_text("<html>old</html>")
                recovered=BridgeCore(root)
                try:
                    self.assertEqual((root/"index.html").read_text(),"<html>new</html>")
                    counts=(recovered.db.execute("SELECT COUNT(*) FROM write_receipts").fetchone()[0],recovered.db.execute("SELECT COUNT(*) FROM events").fetchone()[0],recovered.db.execute("SELECT COUNT(*) FROM publications").fetchone()[0])
                    receipt=json.loads(recovered.db.execute("SELECT result_json FROM write_receipts").fetchone()[0])
                    replay=recovered.save(opened["session_id"],"index.html","<html>new</html>",opened["revision"])
                    self.assertEqual(replay["receipt_id"],receipt["receipt_id"])
                    self.assertEqual((recovered.db.execute("SELECT COUNT(*) FROM write_receipts").fetchone()[0],recovered.db.execute("SELECT COUNT(*) FROM events").fetchone()[0],recovered.db.execute("SELECT COUNT(*) FROM publications").fetchone()[0]),counts)
                finally:recovered.close()
                again=BridgeCore(root)
                try:self.assertEqual((again.db.execute("SELECT COUNT(*) FROM write_receipts").fetchone()[0],again.db.execute("SELECT COUNT(*) FROM events").fetchone()[0],again.db.execute("SELECT COUNT(*) FROM publications").fetchone()[0]),counts)
                finally:again.close()

    def test_third_party_bytes_freeze_recovery(self):
        with tempfile.TemporaryDirectory(prefix="bridge-third-") as tmp:
            root=Path(tmp);self._crash_save(root,"publication.file_applied",0);(root/"index.html").write_text("<html>third-party</html>")
            with self.assertRaises(BridgeError) as caught:BridgeCore(root)
            self.assertEqual(caught.exception.code,"RECOVERY_FAILED")
            self.assertEqual((root/"index.html").read_text(),"<html>third-party</html>")


class SecurityAndMigrationCase(unittest.TestCase):
    def test_hardlink_and_symlink_swap_are_denied(self):
        with tempfile.TemporaryDirectory(prefix="bridge-path-") as tmp,tempfile.TemporaryDirectory(prefix="bridge-out-") as outside:
            root=Path(tmp);(root/"safe").mkdir();(root/"safe/file.txt").write_text("inside");external=Path(outside)/"file.txt";external.write_text("outside")
            core=BridgeCore(root)
            try:
                os.link(root/"safe/file.txt",root/"hard.txt")
                with self.assertRaises(BridgeError):core.secure.read("hard.txt")
                (root/"safe").rename(root/"real-safe");os.symlink(outside,root/"safe")
                with self.assertRaises((BridgeError,OSError)):core.secure.read("safe/file.txt")
                self.assertEqual(external.read_text(),"outside")
            finally:core.close()

    def test_schema_v2_migrates_and_future_schema_is_rejected(self):
        import sqlite3
        with tempfile.TemporaryDirectory(prefix="bridge-migrate-") as tmp:
            internal=Path(tmp)/".pptx-html";internal.mkdir();db=sqlite3.connect(internal/"bridge.sqlite3")
            db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)");db.execute("INSERT INTO meta VALUES('schema_version','2')")
            db.execute("CREATE TABLE attempts(session_id TEXT,intent_id TEXT,attempt INTEGER,base_revision TEXT,work_path TEXT,consumer_id TEXT,status TEXT,result_json TEXT,created_at TEXT,PRIMARY KEY(intent_id,attempt))");db.commit();db.close()
            core=BridgeCore(tmp)
            try:self.assertIn("export_baseline_json",{r[1] for r in core.db.execute("PRAGMA table_info(attempts)")})
            finally:core.close()
        with tempfile.TemporaryDirectory(prefix="bridge-future-") as tmp:
            internal=Path(tmp)/".pptx-html";internal.mkdir();db=sqlite3.connect(internal/"bridge.sqlite3");db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)");db.execute("INSERT INTO meta VALUES('schema_version','999')");db.commit();db.close()
            with self.assertRaises(BridgeError):BridgeCore(tmp)

    def test_svg_active_content_and_unknown_managed_extension_rejected(self):
        with tempfile.TemporaryDirectory(prefix="bridge-svg-") as tmp:
            root=Path(tmp);(root/"assets").mkdir();(root/"index.html").write_text("<html></html>");(root/"assets/x.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>')
            core=BridgeCore(root)
            try:
                with self.assertRaises(BridgeError):core.register_session(deck_path=str(root/"index.html"))
                (root/"assets/x.svg").unlink();(root/"assets/run.exe").write_bytes(b"bad")
                with self.assertRaises(BridgeError):core.register_session(deck_path=str(root/"index.html"))
            finally:core.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
