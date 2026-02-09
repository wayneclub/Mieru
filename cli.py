from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
import pandas as pd

from mieru.io import read_jsonl, to_reviews, write_json, write_jsonl
from mieru.miner import EvidenceMiner, MinerConfig
from mieru.prompts import ASPECTS_DEFAULT, build_consolidation_prompt
from mieru.gemini import generate_json
from mieru.verify import verify_insights


def cmd_mine(args: argparse.Namespace) -> Dict[str, Any]:
    rows = read_jsonl(args.input)
    reviews = to_reviews(rows)

    cfg = MinerConfig(
        top_k_phrases=args.top_k,
        min_df=args.min_df,
        max_phrases_per_review=args.max_phrases_per_review,
        max_sentence_chars=args.max_sentence_chars,
    )
    miner = EvidenceMiner(cfg)
    result = miner.run(reviews)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # candidates.csv
    candidates: pd.DataFrame = result["candidates"]
    candidates_path = out / "candidates.csv"
    candidates.to_csv(candidates_path, index=False, encoding="utf-8")

    # evidence_spans.jsonl
    evidence_spans = result["evidence_spans"]
    ev_rows = [
        {
            "review_id": e.review_id,
            "sentence": e.sentence,
            "rating": e.rating,
        }
        for e in evidence_spans
    ]
    evidence_path = out / "evidence_spans.jsonl"
    write_jsonl(evidence_path, ev_rows)

    # aggregates.csv (optional)
    aggregates: pd.DataFrame = result["aggregates"]
    aggregates_path = out / "aggregates.csv"
    aggregates.to_csv(aggregates_path, index=False, encoding="utf-8")

    return {
        "candidates_path": str(candidates_path),
        "evidence_path": str(evidence_path),
        "aggregates_path": str(aggregates_path),
        "num_evidence_spans": len(ev_rows),
    }


def cmd_consolidate(args: argparse.Namespace) -> Dict[str, Any]:
    mine_out = Path(args.mine_out)
    candidates_path = mine_out / "candidates.csv"
    evidence_path = mine_out / "evidence_spans.jsonl"
    if not candidates_path.exists() or not evidence_path.exists():
        raise FileNotFoundError(
            "mine_out must contain candidates.csv and evidence_spans.jsonl")

    cand = pd.read_csv(candidates_path)
    top_phrases = cand["phrase"].head(args.phrase_k).astype(str).tolist()

    ev_rows = read_jsonl(evidence_path)
    # build indexed evidence strings, keep compact
    indexed = []
    for i, r in enumerate(ev_rows[: args.evidence_k]):
        indexed.append(f"[{i}] {r.get('sentence', '')}")
    prompt = build_consolidation_prompt(
        place_type=args.place_type,
        aspects=ASPECTS_DEFAULT,
        top_phrases=top_phrases,
        evidence_spans=indexed,
    )

    payload = generate_json(prompt)

    ok, errors = verify_insights(payload, num_evidence_spans=len(indexed))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    write_json(out / "insights.json", payload)
    write_json(out / "verify.json", {"ok": ok, "errors": errors})

    return {"ok": ok, "errors": errors, "insights_path": str(out / "insights.json")}


def cmd_run(args: argparse.Namespace) -> None:
    mine_info = cmd_mine(args)
    cons_args = argparse.Namespace(
        mine_out=args.out,
        out=str(Path(args.out) / "consolidated"),
        place_type=args.place_type,
        phrase_k=args.phrase_k,
        evidence_k=args.evidence_k,
    )
    cons_info = cmd_consolidate(cons_args)

    print("✅ Mieru run complete")
    print(f"- candidates: {mine_info['candidates_path']}")
    print(f"- evidence:   {mine_info['evidence_path']}")
    print(f"- insights:   {cons_info['insights_path']}")
    if not cons_info["ok"]:
        print("⚠️ verification failed:")
        for e in cons_info["errors"][:10]:
            print(f"  - {e}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mieru", description="Mieru CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    mine = sub.add_parser(
        "mine", help="Mine evidence spans and candidate phrases.")
    mine.add_argument("--input", "-i", required=True,
                      help="Input reviews JSONL")
    mine.add_argument("--out", "-o", required=True,
                      help="Output directory for mined artifacts")
    mine.add_argument("--top-k", type=int, default=120)
    mine.add_argument("--min-df", type=int, default=2)
    mine.add_argument("--max-phrases-per-review", type=int, default=40)
    mine.add_argument("--max-sentence-chars", type=int, default=300)

    cons = sub.add_parser(
        "consolidate", help="Use Gemini to consolidate into insights.")
    cons.add_argument("--mine-out", required=True,
                      help="Directory produced by mine (contains candidates.csv, evidence_spans.jsonl)")
    cons.add_argument("--out", required=True,
                      help="Output directory for insights.json")
    cons.add_argument("--place-type", default="place",
                      help="restaurant|cafe|hotel|place")
    cons.add_argument("--phrase-k", type=int, default=80,
                      help="Top phrases to pass to Gemini")
    cons.add_argument("--evidence-k", type=int, default=120,
                      help="Evidence spans to pass to Gemini")

    run = sub.add_parser("run", help="One-shot mine + consolidate.")
    run.add_argument("--input", "-i", required=True,
                     help="Input reviews JSONL")
    run.add_argument("--out", "-o", required=True, help="Output directory")
    run.add_argument("--place-type", default="place")
    run.add_argument("--top-k", type=int, default=120)
    run.add_argument("--min-df", type=int, default=2)
    run.add_argument("--max-phrases-per-review", type=int, default=40)
    run.add_argument("--max-sentence-chars", type=int, default=300)
    run.add_argument("--phrase-k", type=int, default=80)
    run.add_argument("--evidence-k", type=int, default=120)

    return p


def main() -> None:
    load_dotenv()  # loads .env if present
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "mine":
        info = cmd_mine(args)
        print("✅ mine complete")
        print(info)
    elif args.cmd == "consolidate":
        info = cmd_consolidate(args)
        print("✅ consolidate complete")
        print(info)
    elif args.cmd == "run":
        cmd_run(args)
    else:
        raise ValueError(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    main()
