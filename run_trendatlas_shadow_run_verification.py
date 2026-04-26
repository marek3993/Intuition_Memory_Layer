from __future__ import annotations

import argparse
from pathlib import Path

from iml.trendatlas_shadow_run import (
    DEFAULT_OUTPUT_DIR,
    build_demo_authoritative_output,
    build_mode_comparison_artifact,
    build_demo_retrieval_request,
    build_shadow_run_artifact,
    seed_demo_store,
    write_mode_comparison_artifacts,
    write_shadow_run_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one TrendAtlas shadow-only retrieval verification and write a manual "
            "inspection artifact without changing authoritative outputs."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write shadow_run_verification.json and .md into.",
    )
    parser.add_argument(
        "--store-path",
        type=Path,
        help="Decision-episode store to read from. Defaults to <output-dir>/demo_store/decision_episodes.jsonl.",
    )
    parser.add_argument(
        "--requester",
        default="planner",
        choices=("planner", "critic", "governor"),
        help="Which TrendAtlas loop to verify in shadow mode.",
    )
    parser.add_argument(
        "--seed-demo-store",
        action="store_true",
        help="Seed an isolated demo store under the output directory before verification.",
    )
    parser.add_argument(
        "--compare-current-winner",
        action="store_true",
        help=(
            "Run a controlled comparison between planner_raw_critic_memory and "
            "planner_raw_critic_memory_gate_v2 for the current requester."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    store_path = args.store_path or output_dir / "demo_store" / "decision_episodes.jsonl"

    if args.seed_demo_store:
        seed_demo_store(store_path)

    if args.compare_current_winner:
        payload = build_mode_comparison_artifact(
            request=build_demo_retrieval_request(requester=args.requester),
            authoritative_output=build_demo_authoritative_output(),
            store_path=store_path,
            output_dir=output_dir,
        )
        written = write_mode_comparison_artifacts(payload, output_dir=output_dir)
        print(f"shadow_mode_compare_json: {written['json_path']}")
        print(f"shadow_mode_compare_markdown: {written['markdown_path']}")
        return 0

    artifact = build_shadow_run_artifact(
        request=build_demo_retrieval_request(requester=args.requester),
        authoritative_output=build_demo_authoritative_output(),
        store_path=store_path,
        output_dir=output_dir,
    )
    written = write_shadow_run_artifacts(artifact, output_dir=output_dir)
    print(f"shadow_run_json: {written['json_path']}")
    print(f"shadow_run_markdown: {written['markdown_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
