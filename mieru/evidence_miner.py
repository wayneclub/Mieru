# evidence_miner.py
"""
EvidenceMiner (Mieru)

Goal:
- Extract high-signal candidate phrases and evidence spans from reviews
- Provide stable, reproducible candidates for Gemini to consolidate
- Do NOT do aspect assignment or sentiment classification (Gemini handles semantics)

Outputs:
- candidates_df: phrase-level candidates with TF-IDF / frequency signals
- aggregates_df: noun-centered aggregation (adjective modifiers counts)
- evidence_spans: list of evidence spans (review_id + sentence) for grounding
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple, Any
from collections import Counter, defaultdict
import re
import math

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


# -----------------------------
# Config structures
# -----------------------------

@dataclass(frozen=True)
class ReviewRecord:
    review_id: str
    text: str
    rating: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class EvidenceSpan:
    review_id: str
    sentence: str
    raw_text: str
    rating: Optional[float] = None


@dataclass
class MinerConfig:
    # phrase protection: "customer service" -> "customer_service"
    protected_phrases: Dict[str, str]

    # minimal stopwords, keep it small (platform noise + generic verbs)
    stopwords: List[str]

    # TF-IDF + frequency knobs
    max_phrases_per_review: int = 30
    top_k_phrases: int = 80
    min_df: int = 2

    # sentence splitting / cleanup
    max_sentence_chars: int = 300
    min_phrase_len: int = 2
    max_phrase_len: int = 6

    # candidate phrase patterns
    allow_adj_noun: bool = True
    allow_noun_phrases: bool = True


# -----------------------------
# Lightweight preprocessing
# -----------------------------

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z'\-]*")


def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def protect_phrases(text: str, protected_map: Dict[str, str]) -> str:
    """
    Replace protected multiword phrases with underscored tokens.
    This is not to 'teach the model' but to stabilize evidence/candidate matching.
    """
    # Longest-first replacement to avoid partial overlaps
    # Example: "value for money" before "value"
    items = sorted(protected_map.items(),
                   key=lambda kv: len(kv[0]), reverse=True)
    out = " " + text + " "
    lowered = out.lower()

    # Do replacement on a lowercase buffer to match case-insensitively,
    # but preserve original text shape is not required for extraction.
    for src, dst in items:
        src_l = " " + src.lower().strip() + " "
        if src_l in lowered:
            out = re.sub(rf"(?i)\b{re.escape(src.strip())}\b", dst, out)
            lowered = out.lower()

    return _normalize_ws(out)


def clean_text(text: str) -> str:
    """
    Minimal cleanup for extraction. Keep it conservative.
    """
    t = text.replace("\u2019", "'").replace(
        "\u201c", '"').replace("\u201d", '"')
    t = re.sub(r"http\S+", " ", t)
    t = re.sub(r"[\t\r]+", " ", t)
    t = _normalize_ws(t)
    return t


def split_sentences(text: str) -> List[str]:
    """
    Simple sentence splitter. You can replace with spaCy later,
    but this is good enough for stable evidence spans in hackathon context.
    """
    # Split on ., !, ? plus line breaks
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    sents = [_normalize_ws(p) for p in parts if _normalize_ws(p)]
    return sents


def tokenize_words(text: str) -> List[str]:
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


# -----------------------------
# Candidate phrase extraction
# -----------------------------

_ADJ_SUFFIX = ("y", "ful", "less", "ous", "ive", "able", "ible", "ic", "al")


def _looks_like_adj(w: str) -> bool:
    # Very lightweight heuristic; Gemini will handle semantics later.
    return len(w) >= 3 and w.endswith(_ADJ_SUFFIX)


def _is_stopword(w: str, stopset: set) -> bool:
    return w in stopset or len(w) <= 1


def extract_adj_noun_phrases(tokens: List[str], stopset: set,
                             min_len: int, max_len: int) -> List[Tuple[str, str]]:
    """
    Extract (adj, noun) pairs using a simple heuristic:
    - adjective-like token followed by a noun-like token
    - noun-like token is any non-stopword token
    Returns list of (adj, noun) pairs; both already lowercase/underscored.
    """
    pairs: List[Tuple[str, str]] = []
    for i in range(len(tokens) - 1):
        a, n = tokens[i], tokens[i + 1]
        if _is_stopword(a, stopset) or _is_stopword(n, stopset):
            continue
        if not _looks_like_adj(a):
            continue
        # treat next token as noun candidate
        if min_len <= len(n.split("_")) <= max_len:
            pairs.append((a, n))
    return pairs


def extract_noun_phrases(tokens: List[str], stopset: set,
                         min_len: int, max_len: int) -> List[str]:
    """
    Extract simple noun phrase candidates:
    - sequences of 1..N tokens that are not stopwords
    - includes underscored protected phrases as single token
    """
    out: List[str] = []
    buff: List[str] = []

    def flush():
        nonlocal buff
        if buff:
            # keep shortest useful unit as single token phrase
            # (Gemini will merge/cluster variants later)
            out.append("_".join(buff))
            buff = []

    for tok in tokens:
        if _is_stopword(tok, stopset):
            flush()
            continue
        # protected phrase already has underscores; treat as atomic
        if "_" in tok:
            flush()
            out.append(tok)
            continue
        buff.append(tok)
        if len(buff) >= max_len:
            flush()
    flush()

    # filter length
    filtered = []
    for p in out:
        n_words = len(p.split("_"))
        if min_len <= n_words <= max_len:
            filtered.append(p)
    return filtered


# -----------------------------
# TF-IDF ranking over candidates
# -----------------------------

def _tfidf_rank(docs: List[List[str]], min_df: int) -> pd.DataFrame:
    """
    docs: list of list-of-phrases (already underscored tokens)
    Returns a phrase-level TF-IDF score table
    """
    joined = [" ".join(d) for d in docs]
    if not joined:
        return pd.DataFrame(columns=["phrase", "tfidf"])

    # cap min_df
    min_df_eff = min(min_df, max(1, len(joined)))

    vec = TfidfVectorizer(
        tokenizer=lambda s: s.split(),
        token_pattern=None,
        lowercase=False,
        min_df=min_df_eff,
    )
    X = vec.fit_transform(joined)
    feats = vec.get_feature_names_out()
    # mean tf-idf across documents
    scores = np.asarray(X.mean(axis=0)).ravel()

    df = pd.DataFrame({"phrase": feats, "tfidf": scores})
    df = df.sort_values("tfidf", ascending=False).reset_index(drop=True)
    return df


# -----------------------------
# Main miner
# -----------------------------

class EvidenceMiner:
    """
    Pipeline:
      1) preprocess -> clean + protect
      2) sentence split -> evidence spans
      3) phrase candidate extraction (adj-noun + noun phrases)
      4) TF-IDF ranking + frequency stats
      5) noun-centered aggregation (adj->noun counts)

    The output is designed to feed Gemini consolidation.
    """

    def __init__(self, config: MinerConfig) -> None:
        self.cfg = config
        self.stopset = set(w.strip().lower() for w in (config.stopwords or []))

    def run(self, reviews: List[ReviewRecord]) -> Dict[str, Any]:
        evidence_spans: List[EvidenceSpan] = []
        per_review_phrase_docs: List[List[str]] = []
        phrase_freq = Counter()
        noun_adj_counts: Dict[str, Counter] = defaultdict(Counter)

        for r in reviews:
            raw = r.text or ""
            if not raw.strip():
                continue

            cleaned = clean_text(raw)
            protected = protect_phrases(cleaned, self.cfg.protected_phrases)

            # evidence spans
            sents = split_sentences(protected)
            for s in sents:
                if not s:
                    continue
                if len(s) > self.cfg.max_sentence_chars:
                    s = s[: self.cfg.max_sentence_chars].strip()
                evidence_spans.append(EvidenceSpan(
                    review_id=r.review_id,
                    sentence=s,
                    raw_text=raw,
                    rating=r.rating,
                ))

            # phrase candidates for this review
            tokens = tokenize_words(protected)

            phrases: List[str] = []
            if self.cfg.allow_adj_noun:
                pairs = extract_adj_noun_phrases(tokens, self.stopset,
                                                 self.cfg.min_phrase_len,
                                                 self.cfg.max_phrase_len)
                # store as "adj_noun" phrase tokens for stable matching
                for adj, noun in pairs:
                    # skip if noun is too generic
                    if _is_stopword(noun, self.stopset):
                        continue
                    phrases.append(f"{adj}_{noun}")
                    noun_adj_counts[noun][adj] += 1

            if self.cfg.allow_noun_phrases:
                nps = extract_noun_phrases(tokens, self.stopset,
                                           self.cfg.min_phrase_len,
                                           self.cfg.max_phrase_len)
                phrases.extend(nps)

            # de-dup per review, keep top N by local frequency
            # (local frequency is crude but stabilizes docs for TF-IDF)
            local = Counter(phrases)
            top_local = [p for p, _ in local.most_common(
                self.cfg.max_phrases_per_review)]
            per_review_phrase_docs.append(top_local)

            phrase_freq.update(top_local)

        # rank phrases
        tfidf_df = _tfidf_rank(per_review_phrase_docs, self.cfg.min_df)
        if tfidf_df.empty:
            candidates_df = pd.DataFrame(
                columns=["phrase", "tfidf", "freq", "score"])
        else:
            tfidf_df["freq"] = tfidf_df["phrase"].map(
                lambda p: phrase_freq.get(p, 0)).astype(int)
            # blended score: prioritize tfidf but keep frequency as stabilizer
            # score = tfidf * log(1 + freq)
            tfidf_df["score"] = tfidf_df["tfidf"] * np.log1p(tfidf_df["freq"])
            candidates_df = tfidf_df.sort_values(
                "score", ascending=False).reset_index(drop=True)

        # keep top-K
        candidates_df = candidates_df.head(self.cfg.top_k_phrases).copy()

        # aggregation table: noun -> top adjectives (for UI or Gemini hints)
        rows = []
        for noun, adj_counter in noun_adj_counts.items():
            total = sum(adj_counter.values())
            top_adjs = adj_counter.most_common(5)
            rows.append({
                "noun": noun,
                "total_modifiers": total,
                "top_adjectives": ", ".join([f"{a}({c})" for a, c in top_adjs]),
            })
        aggregates_df = pd.DataFrame(rows).sort_values(
            "total_modifiers", ascending=False
        ).reset_index(drop=True)

        return {
            "candidates": candidates_df,
            "aggregates": aggregates_df,
            "evidence_spans": [e.__dict__ for e in evidence_spans],
        }


# -----------------------------
# Optional helper: build ReviewRecord list from your unified schema
# -----------------------------

def from_unified_reviews(reviews: List[Dict[str, Any]]) -> List[ReviewRecord]:
    """
    Convert your existing unified review dicts into ReviewRecord.
    Expected keys: id/text/rating (adjust mapping if needed)
    """
    out: List[ReviewRecord] = []
    for i, r in enumerate(reviews):
        rid = str(r.get("review_id") or r.get("id") or i)
        text = str(r.get("text") or "")
        rating = r.get("rating")
        try:
            rating_f = float(rating) if rating is not None else None
        except Exception:
            rating_f = None
        out.append(ReviewRecord(review_id=rid,
                   text=text, rating=rating_f, meta=r))
    return out
