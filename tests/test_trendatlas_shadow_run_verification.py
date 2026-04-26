from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path

from iml.trendatlas_shadow_run import (
    build_demo_authoritative_output,
    build_mode_comparison_artifact,
    build_demo_retrieval_request,
    build_shadow_run_artifact,
    render_shadow_run_markdown,
    seed_demo_store,
    write_mode_comparison_artifacts,
    write_shadow_run_artifacts,
)


class TrendAtlasShadowRunVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        workspace_temp_root = Path.cwd() / ".tmp_test_trendatlas_live_write"
        workspace_temp_root.mkdir(exist_ok=True)
        self.tempdir = workspace_temp_root / f"shadow_{uuid.uuid4().hex}"
        self.tempdir.mkdir()
        self.addCleanup(lambda: shutil.rmtree(self.tempdir, ignore_errors=True))
        self.store_path = self.tempdir / "decision_episodes.jsonl"

    def test_shadow_run_preserves_authoritative_output_and_selects_shadow_matches(self) -> None:
        seed_demo_store(self.store_path)

        authoritative_output = build_demo_authoritative_output()
        artifact = build_shadow_run_artifact(
            request=build_demo_retrieval_request(requester="planner"),
            authoritative_output=authoritative_output,
            store_path=self.store_path,
            output_dir=self.tempdir,
            now_utc="2026-04-21T12:00:00Z",
        )

        self.assertEqual(
            artifact["authoritative_baseline_path_used"]["output"],
            authoritative_output,
        )
        self.assertEqual(
            artifact["final_authoritative_output"]["output"],
            authoritative_output,
        )
        self.assertTrue(artifact["comparison_result_summary"]["authoritative_output_preserved"])
        self.assertGreater(
            artifact["comparison_result_summary"]["retrieval_match_count"],
            0,
        )
        self.assertFalse(artifact["fail_closed_status"]["triggered"])
        self.assertEqual(
            artifact["shadow_comparison_path_used"]["response"]["matches"][0]["episode_type"],
            "governor_decision",
        )

    def test_shadow_run_fail_closes_when_store_is_unavailable(self) -> None:
        authoritative_output = build_demo_authoritative_output()
        artifact = build_shadow_run_artifact(
            request=build_demo_retrieval_request(requester="planner"),
            authoritative_output=authoritative_output,
            store_path=self.store_path,
            output_dir=self.tempdir,
            now_utc="2026-04-21T12:00:00Z",
        )

        self.assertTrue(artifact["fail_closed_status"]["triggered"])
        self.assertEqual(
            artifact["final_authoritative_output"]["output"],
            authoritative_output,
        )
        self.assertEqual(
            artifact["shadow_comparison_path_used"]["response"]["matches"],
            [],
        )
        self.assertIn("fail_closed_triggered", artifact["divergence_markers"])
        self.assertIsNotNone(artifact["retrieval_error"])

    def test_write_shadow_run_artifacts_emits_manual_inspection_files(self) -> None:
        seed_demo_store(self.store_path)
        artifact = build_shadow_run_artifact(
            request=build_demo_retrieval_request(requester="critic"),
            authoritative_output=build_demo_authoritative_output(),
            store_path=self.store_path,
            output_dir=self.tempdir,
            now_utc="2026-04-21T12:00:00Z",
        )

        written = write_shadow_run_artifacts(artifact, output_dir=self.tempdir)
        json_path = Path(written["json_path"])
        markdown_path = Path(written["markdown_path"])

        self.assertTrue(json_path.exists())
        self.assertTrue(markdown_path.exists())
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("authoritative_baseline_path_used", payload)
        self.assertIn("shadow_comparison_path_used", payload)
        self.assertIn("comparison_result_summary", payload)
        self.assertIn("critic_memory_gate_observability", payload)
        self.assertIn("fail_closed_status", payload)
        self.assertIn("TrendAtlas Shadow Run Verification", markdown)
        self.assertIn("Fail-Closed Status", markdown)
        self.assertIn("Gate decision", markdown)

    def test_render_shadow_run_markdown_mentions_selected_inputs(self) -> None:
        seed_demo_store(self.store_path)
        artifact = build_shadow_run_artifact(
            request=build_demo_retrieval_request(requester="governor"),
            authoritative_output=build_demo_authoritative_output(),
            store_path=self.store_path,
            output_dir=self.tempdir,
            now_utc="2026-04-21T12:00:00Z",
        )

        markdown = render_shadow_run_markdown(artifact)
        self.assertIn("Retrieval Inputs Selected", markdown)
        self.assertIn("Authoritative baseline path used", markdown)
        self.assertIn("Shadow comparison path used", markdown)

    def test_critic_gate_v2_turns_retrieval_off_on_obvious_low_value_case(self) -> None:
        seed_demo_store(self.store_path)
        request = build_demo_retrieval_request(requester="critic")
        request["query_context"]["goal"] = "Provide a straightforward routine review with low risk."
        request["query_context"]["current_packet_text"] = (
            "This is a settled case with a clear pass and no extra policy concerns."
        )

        artifact = build_shadow_run_artifact(
            request=request,
            authoritative_output=build_demo_authoritative_output(),
            store_path=self.store_path,
            output_dir=self.tempdir,
            mode_id="planner_raw_critic_memory_gate_v2",
            enable_critic_gate_v2=True,
            now_utc="2026-04-21T12:00:00Z",
        )

        gate = artifact["critic_memory_gate_observability"]
        self.assertEqual(gate["gate_decision"], "off")
        self.assertIn("obvious_raw_case_skip", gate["gate_reason_codes"])
        self.assertFalse(gate["retrieval_attempted"])
        self.assertFalse(gate["retrieval_attached"])
        self.assertTrue(artifact["fail_closed_status"]["triggered"])
        self.assertEqual(
            artifact["final_authoritative_output"]["output"],
            build_demo_authoritative_output(),
        )

    def test_critic_gate_v2_preserves_fail_closed_when_inputs_are_unavailable(self) -> None:
        seed_demo_store(self.store_path)
        request = build_demo_retrieval_request(requester="critic")
        request["query_context"] = {}

        artifact = build_shadow_run_artifact(
            request=request,
            authoritative_output=build_demo_authoritative_output(),
            store_path=self.store_path,
            output_dir=self.tempdir,
            mode_id="planner_raw_critic_memory_gate_v2",
            enable_critic_gate_v2=True,
            now_utc="2026-04-21T12:00:00Z",
        )

        gate = artifact["critic_memory_gate_observability"]
        self.assertEqual(gate["gate_decision"], "off")
        self.assertIn("gate_inputs_unavailable", gate["gate_reason_codes"])
        self.assertFalse(gate["retrieval_attempted"])
        self.assertFalse(gate["retrieval_attached"])
        self.assertTrue(artifact["fail_closed_status"]["triggered"])
        self.assertEqual(
            artifact["comparison_result_summary"]["authoritative_output_unchanged"],
            True,
        )

    def test_critic_gate_v2_emits_observability_without_mutating_authoritative_output(self) -> None:
        seed_demo_store(self.store_path)
        authoritative_output = build_demo_authoritative_output()
        artifact = build_shadow_run_artifact(
            request=build_demo_retrieval_request(requester="critic"),
            authoritative_output=authoritative_output,
            store_path=self.store_path,
            output_dir=self.tempdir,
            mode_id="planner_raw_critic_memory_gate_v2",
            enable_critic_gate_v2=True,
            now_utc="2026-04-21T12:00:00Z",
        )

        gate = artifact["critic_memory_gate_observability"]
        self.assertEqual(gate["gate_decision"], "on")
        self.assertTrue(gate["retrieval_attempted"])
        self.assertTrue(gate["retrieval_attached"])
        self.assertTrue(gate["authoritative_output_unchanged"])
        self.assertIn("strong_prior_episode_match", gate["gate_reason_codes"])
        self.assertIn("high_value_prior_pattern", gate["gate_reason_codes"])
        self.assertEqual(
            artifact["final_authoritative_output"]["output"],
            authoritative_output,
        )
        self.assertEqual(
            artifact["comparison_result_summary"]["retrieval_attached"],
            True,
        )

    def test_mode_comparison_artifacts_compare_current_winner_to_gate_v2(self) -> None:
        seed_demo_store(self.store_path)
        payload = build_mode_comparison_artifact(
            request=build_demo_retrieval_request(requester="critic"),
            authoritative_output=build_demo_authoritative_output(),
            store_path=self.store_path,
            output_dir=self.tempdir,
            now_utc="2026-04-21T12:00:00Z",
        )

        self.assertEqual(payload["current_winner_mode"], "planner_raw_critic_memory")
        self.assertEqual(payload["challenger_mode"], "planner_raw_critic_memory_gate_v2")
        self.assertTrue(payload["comparison_summary"]["authoritative_output_unchanged_in_both"])
        self.assertTrue(payload["comparison_summary"]["final_authoritative_outputs_equal"])

        written = write_mode_comparison_artifacts(payload, output_dir=self.tempdir)
        self.assertTrue(Path(written["json_path"]).exists())
        self.assertTrue(Path(written["markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
