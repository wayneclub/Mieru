from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .types import Review


def read_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input not found: {p}")

    rows: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def to_reviews(rows: List[Dict[str, Any]]) -> List[Review]:
    out: List[Review] = []
    for i, r in enumerate(rows):
        rid = str(r.get("review_id") or r.get("id") or i)
        text = str(r.get("text") or "")
        if not text.strip():
            continue
        rating = r.get("rating", None)
        try:
            rating_f = float(rating) if rating is not None else None
        except Exception:
            rating_f = None
        out.append(Review(review_id=rid, text=text, rating=rating_f, meta=r))
    return out


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_jsonl(path: str | Path, rows: Iterable[Dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
