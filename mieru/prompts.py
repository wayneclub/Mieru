from __future__ import annotations

from typing import List


ASPECTS_DEFAULT = [
    "quality",        # food quality / room quality / product quality
    "service",
    "cleanliness",
    "noise",
    "value",
    "wait_speed",     # wait time / check-in speed / service speed
    "location",
    "amenities",      # wifi, outlets, parking, gym, etc.
]


def build_consolidation_prompt(
    place_type: str,
    aspects: List[str],
    top_phrases: List[str],
    evidence_spans: List[str],
) -> str:
    # Keep prompt compact; you can tune later
    aspect_list = ", ".join(aspects)

    return f"""
You are helping build a review intelligence system for {place_type}.
Your task is to turn noisy review text into grounded, verifiable insights.

Constraints:
- Only use information supported by the provided evidence spans.
- Every claim MUST cite at least one evidence span index.
- Prefer concise, decision-useful claims. Avoid generic statements.
- If evidence is mixed or weak, include an uncertainty note.

Output MUST be valid JSON (no markdown). Use this schema:

{{
  "concepts": [
    {{
      "concept": "canonical short phrase in lowercase",
      "variants": ["variant phrase 1", "variant phrase 2"],
      "aspects": ["one or more from: {aspect_list}"]
    }}
  ],
  "insights": [
    {{
      "aspect": "one from: {aspect_list}",
      "summary": "2-3 sentences max",
      "claims": [
        {{
          "text": "a specific claim",
          "polarity": "positive|negative|mixed|neutral",
          "evidence": [0, 3, 8],
          "support": "high|medium|low"
        }}
      ],
      "uncertainties": ["optional list of uncertainty notes"]
    }}
  ]
}}

Inputs:
Top phrases (candidates):
{top_phrases}

Evidence spans (indexed):
{evidence_spans}
""".strip()
