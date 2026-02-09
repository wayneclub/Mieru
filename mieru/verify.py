from __future__ import annotations

from typing import Any, Dict, List, Tuple


def verify_insights(payload: Dict[str, Any], num_evidence_spans: int) -> Tuple[bool, List[str]]:
    """
    Minimal verification:
    - payload has "insights" list
    - each claim has evidence list with valid indices
    """
    errors: List[str] = []

    if not isinstance(payload, dict):
        return False, ["payload is not a dict"]

    insights = payload.get("insights")
    if not isinstance(insights, list):
        return False, ["payload.insights must be a list"]

    for i, ins in enumerate(insights):
        claims = ins.get("claims", [])
        if not isinstance(claims, list) or len(claims) == 0:
            errors.append(f"insights[{i}] has no claims")
            continue

        for j, c in enumerate(claims):
            ev = c.get("evidence")
            if not isinstance(ev, list) or len(ev) == 0:
                errors.append(f"insights[{i}].claims[{j}] missing evidence")
                continue
            for k, idx in enumerate(ev):
                if not isinstance(idx, int):
                    errors.append(
                        f"insights[{i}].claims[{j}].evidence[{k}] not int")
                    continue
                if idx < 0 or idx >= num_evidence_spans:
                    errors.append(
                        f"insights[{i}].claims[{j}].evidence[{k}] out of range")

    return (len(errors) == 0), errors
