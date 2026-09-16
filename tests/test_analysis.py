import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
from pathlib import Path

import networkx as nx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.analysis import correlate
from src.data_loader import load_dataset
from src.models import Alarm
from src.rca_explanation import explain_metrics
from src import mcp_server

ROOT = Path(__file__).resolve().parents[1]


def alarm(identifier, service, minute=0, severity=5, kind="timeout"):
    return Alarm(identifier, datetime(2026, 9, 10, 2) + timedelta(minutes=minute),
                 "test", service + "-host", service, severity, kind, "test", {})


class AnalysisTests(unittest.TestCase):
    def test_dependency_direction_and_no_symptom_loss(self):
        result = correlate([alarm("a", "A"), alarm("b", "B")], nx.DiGraph([("A", "B")]))
        card = result["event_cards"][0]
        self.assertEqual(card["root_service"], "B")
        self.assertEqual(card["derived_alarm_ids"], ["a"])
        self.assertEqual(result["noise_audit_log"], [])

    def test_boundary_and_slow_episode(self):
        rows = [alarm(str(i), "B", i) for i in (9, 11, 20, 29, 38, 47)]
        result = correlate(rows, nx.DiGraph())
        self.assertEqual(len(result["event_cards"]), 1)
        self.assertTrue(result["event_cards"][0]["long_running"])

    def test_separate_incidents_after_gap(self):
        result = correlate([alarm("a", "B"), alarm("b", "B", 60)], nx.DiGraph())
        self.assertEqual(len(result["event_cards"]), 2)

    def test_cycle_is_ambiguous(self):
        graph = nx.DiGraph([("A", "B"), ("B", "A")])
        result = correlate([alarm("a", "A"), alarm("b", "B")], graph)
        self.assertTrue(result["rca_metrics"]["EVT-001"]["cycle_ambiguity"])

    def test_noise_and_isolated_critical(self):
        result = correlate([alarm("n", "N", severity=1, kind="log_rotate"),
                            alarm("c", "C")], nx.DiGraph())
        self.assertEqual([x["alarm_id"] for x in result["noise_audit_log"]], ["n"])
        self.assertEqual(result["event_cards"][0]["root_service"], "C")
        evidence = result["noise_audit_log"][0]["evidence"]
        self.assertEqual(evidence["severity"], 1)
        self.assertEqual(evidence["checked_services"], ["N"])
        self.assertEqual(evidence["nearby_strong_signal_count"], 0)

    def test_empty_and_invalid_limit(self):
        self.assertEqual(correlate([], nx.DiGraph())["event_cards"], [])
        for limit in (0, -1, True, 1.5, None, 16):
            with self.assertRaises(ValueError):
                correlate([], nx.DiGraph(), max_cards=limit)

    def test_limit_never_discards_or_calls_overflow_noise(self):
        result = correlate([alarm(str(i), str(i)) for i in range(16)], nx.DiGraph(), max_cards=15)
        self.assertEqual(len(result["event_cards"]), 15)
        self.assertEqual(len(result["deferred_incidents"]), 1)
        self.assertEqual(result["noise_audit_log"], [])
        self.assertEqual(result["correlation_summary"]["accounted_alarm_count"], 16)

    def test_upper_bound_and_required_schema(self):
        result = correlate([alarm(str(i), str(i)) for i in range(20)], nx.DiGraph())
        self.assertEqual(len(result["event_cards"]), 15)
        self.assertEqual(result["correlation_summary"]["max_event_card_limit"], 15)
        self.assertEqual(len(result["deferred_incidents"]), 5)
        self.assertTrue(result["warnings"])
        for card in result["event_cards"]:
            self.assertTrue(card["root_cause_hypothesis"])
            self.assertTrue(card["impacted_services"])
            self.assertEqual(card["alarm_count_total"], len(card["alarm_ids"]))
            self.assertEqual(set(card["time_window"]), {"start", "end"})
            self.assertTrue(card["action"]["first_action"])
            self.assertTrue(card["action"]["owner"])
            self.assertEqual(card["action"]["status"], "Açık")

    def test_natural_language_rca_and_counter_evidence(self):
        result = correlate([alarm("a", "A"), alarm("b", "B")], nx.DiGraph([("A", "B")]))
        explanation = explain_metrics(result["rca_metrics"]["EVT-001"])
        self.assertIn("b", explanation["explanation"])
        alternative = explanation["counter_hypotheses"][0]
        self.assertEqual(alternative["graph_paths"], [["A", "B"]])
        self.assertEqual(alternative["evidence_alarm_ids"], ["a"])
        self.assertIn("elenmedi", alternative["assessment"])

    def test_all_dataset_records_and_determinism(self):
        rows, graph, inventory = load_dataset(ROOT / "data")
        result = correlate(rows, graph, inventory)
        self.assertEqual(len(rows), 3000)
        self.assertEqual(result["correlation_summary"]["accounted_alarm_count"], 3000)
        self.assertFalse(result["deferred_incidents"])
        self.assertEqual(result["correlation_summary"]["max_event_card_limit"], 15)
        self.assertLessEqual(len(result["event_cards"]), 15)
        self.assertEqual(result, correlate(list(reversed(rows)), graph, inventory))
        ids = [a["alarm_id"] for m in result["rca_metrics"].values() for a in m["alarms"]]
        ids += [a["alarm_id"] for a in result["noise_audit_log"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {a.alarm_id for a in rows})
        json.dumps(result, allow_nan=False)

    def test_cli_uses_same_engine(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            completed = subprocess.run([
                sys.executable, "-m", "src.main", "--data-dir", str(ROOT / "data"),
                "--out-json", str(output / "cards.json"),
                "--out-html", str(output / "cards.html"),
            ], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads((output / "analysis_result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["correlation_summary"]["accounted_alarm_count"], 3000)


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.saved = mcp_server._result
        mcp_server._result = None

    def tearDown(self):
        mcp_server._result = self.saved

    def test_status_survives_rerank_but_not_changed_evidence(self):
        rows = [alarm("b", "B")]
        with patch.object(mcp_server, "load_dataset", return_value=(rows, nx.DiGraph(), {})):
            result = mcp_server.update_action_status("EVT-001", "Kapalı")
            self.assertTrue(result["changed"])
            result["action"]["status"] = "Açık"
            self.assertEqual(mcp_server.explain_root_cause("EVT-001")["event_card"]["action"]["status"], "Kapalı")
        rows = [alarm("a", "A"), alarm("b", "B")]
        with patch.object(mcp_server, "load_dataset", return_value=(rows, nx.DiGraph(), {})):
            cards = mcp_server.load_and_correlate_alerts()["event_cards"]
            self.assertEqual({c["root_service"]: c["action"]["status"] for c in cards}, {"A": "Açık", "B": "Kapalı"})
        rows[-1].message = "changed evidence"
        with patch.object(mcp_server, "load_dataset", return_value=(rows, nx.DiGraph(), {})):
            cards = mcp_server.load_and_correlate_alerts()["event_cards"]
            self.assertTrue(all(c["action"]["status"] == "Açık" for c in cards))

    def test_invalid_status_and_id_do_not_mutate(self):
        with patch.object(mcp_server, "load_dataset", return_value=([alarm("b", "B")], nx.DiGraph(), {})):
            mcp_server.load_and_correlate_alerts()
            before = mcp_server._snapshot()
            for identifier, status in (("missing", "Kapalı"), ("EVT-001", "invalid")):
                with self.assertRaises(ValueError):
                    mcp_server.update_action_status(identifier, status)
            self.assertEqual(mcp_server._snapshot(), before)


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_handshake_and_all_tools(self):
        params = StdioServerParameters(command=sys.executable,
            args=["-m", "src.mcp_server"], cwd=str(ROOT))
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                self.assertEqual({tool.name for tool in tools.tools}, {
                    "load_and_correlate_alerts", "get_noise_audit_log", "explain_root_cause",
                    "update_action_status"
                })
                # Audit ilk çağrı olduğunda da veri yüklenmelidir.
                audit = await session.call_tool("get_noise_audit_log", {})
                self.assertFalse(audit.isError)
                result = await session.call_tool("load_and_correlate_alerts", {})
                self.assertFalse(result.isError)
                payload = json.loads(result.content[0].text)
                self.assertEqual(payload["dataset"]["total_alarms"], 3000)
                for card in payload["event_cards"]:
                    explanation = await session.call_tool("explain_root_cause", {"event_id": card["event_id"]})
                    self.assertFalse(explanation.isError)
                    metrics = json.loads(explanation.content[0].text)
                    self.assertEqual(len(metrics["alarms"]), card["alarm_count_total"])
                    self.assertTrue(metrics["explanation"])
                    self.assertTrue(metrics["counter_hypotheses"])
                event_id = payload["event_cards"][0]["event_id"]
                for status in ("İnceleniyor", "Müdahale Ediliyor", "Kapalı", "Kapalı", "Açık"):
                    update = await session.call_tool("update_action_status", {"event_id": event_id, "new_status": status})
                    self.assertFalse(update.isError)
                    self.assertEqual(json.loads(update.content[0].text)["action"]["status"], status)
                refreshed = await session.call_tool("load_and_correlate_alerts", {})
                card = json.loads(refreshed.content[0].text)["event_cards"][0]
                self.assertEqual(len(card["action"]["history"]), 4)
                invalid_status = await session.call_tool("update_action_status", {"event_id": event_id, "new_status": "invalid"})
                self.assertTrue(invalid_status.isError)
                invalid_id = await session.call_tool("update_action_status", {"event_id": "missing", "new_status": "Kapalı"})
                self.assertTrue(invalid_id.isError)
                invalid = await session.call_tool("explain_root_cause", {"event_id": "missing"})
                self.assertTrue(invalid.isError)


if __name__ == "__main__":
    unittest.main()