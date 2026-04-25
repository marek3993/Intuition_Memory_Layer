from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path

from iml.trendatlas_shadow_run import (
    build_demo_authoritative_output,
    build_demo_retrieval_request,
    build_shadow_run_artifact,
    render_shadow_run_markdown,
    seed_demo_store,
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
        self.assertIn("fail_closed_status", payload)
        self.assertIn("TrendAtlas Shadow Run Verification", markdown)
        self.assertIn("Fail-Closed Status", markdown)

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


if __name__ == "__main__":
    unittest.main()
