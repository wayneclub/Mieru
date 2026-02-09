from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from .types import Review, EvidenceSpan


_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z'\-]*")


@dataclass
class MinerConfig:
    top_k_phrases: int = 120
    min_df: int = 2
    max_phrases_per_review: int = 40
    max_sentence_chars: int = 300

    # Keep stopwords minimal (platform noise + generic verbs)
    stopwords: Optional[List[str]] = None

    # Basic extraction toggles
    enable_adj_noun: bool = True
    enable_noun_phrases: bool = True


def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def clean_text(text: str) -> str:
    t = text.replace("\u2019", "'").replace(
        "\u201c", '"').replace("\u201d", '"')
    t = re.sub(r"http\S+", " ", t)
    t = re.sub(r"[\t\r]+", " ", t)
    return _normalize_ws(t)


def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [_normalize_ws(p) for p in parts if _normalize_ws(p)]


def tokenize(text: str) -> List[str]:
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


_ADJ_SUFFIX = ("y", "ful", "less", "ous", "ive", "able", "ible", "ic", "al")


def looks_like_adj(w: str) -> bool:
    return len(w) >= 3 and w.endswith(_ADJ_SUFFIX)


def default_stopwords() -> List[str]:
    # Minimal list; expand only if you truly need it
    return [
        "google", "maps", "yelp", "review", "reviews", "star", "stars", "rating", "ratings",
        "place", "places", "people", "time", "times",
        "go", "went", "come", "came", "get", "got", "make", "made", "take", "took",
        "really", "very", "just", "like", "also",
        "the", "a", "an", "and", "or", "but", "if", "then",
        "to", "of", "in", "on", "at", "for", "with", "from", "as", "by",
        "is", "are", "was", "were", "be", "been",
    ]


def extract_adj_noun_pairs(tokens: List[str], stopset: set) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for i in range(len(tokens) - 1):
        a, n = tokens[i], tokens[i + 1]
        if a in stopset or n in stopset:
            continue
        if not looks_like_adj(a):
            continue
        pairs.append((a, n))
    return pairs


def extract_noun_phrases(tokens: List[str], stopset: set, max_len: int = 4) -> List[str]:
    # Simple chunker: sequences of non-stopwords
    out: List[str] = []
    buff: List[str] = []

    def flush():
        nonlocal buff
        if buff:
            out.append("_".join(buff))
            buff = []

    for tok in tokens:
        if tok in stopset:
            flush()
            continue
        buff.append(tok)
        if len(buff) >= max_len:
            flush()
    flush()

    # Keep 1..4 word phrases
    filtered = []
    for p in out:
        n_words = len(p.split("_"))
        if 1 <= n_words <= max_len:
            filtered.append(p)
    return filtered


def tfidf_rank(docs: List[List[str]], min_df: int) -> pd.DataFrame:
    joined = [" ".join(d) for d in docs]
    if not joined:
        return pd.DataFrame(columns=["phrase", "tfidf"])

    min_df_eff = min(min_df, max(1, len(joined)))
    vec = TfidfVectorizer(
        tokenizer=lambda s: s.split(),
        token_pattern=None,
        lowercase=False,
        min_df=min_df_eff,
    )
    X = vec.fit_transform(joined)
    feats = vec.get_feature_names_out()
    scores = np.asarray(X.mean(axis=0)).ravel()

    df = pd.DataFrame({"phrase": feats, "tfidf": scores})
    return df.sort_values("tfidf", ascending=False).reset_index(drop=True)


class EvidenceMiner:
    """
    Output:
      - candidates (DataFrame): phrase, tfidf, freq, score
      - evidence_spans (list[EvidenceSpan]): sentence-level spans for grounding
      - aggregates (DataFrame): noun -> top adjectives (optional signal)
    """

    def __init__(self, cfg: MinerConfig) -> None:
        self.cfg = cfg
        sw = cfg.stopwords if cfg.stopwords is not None else default_stopwords()
        self.stopset = set(s.lower().strip() for s in sw if s.strip())

    def run(self, reviews: List[Review]) -> Dict[str, Any]:
        evidence_spans: List[EvidenceSpan] = []
        per_review_docs: List[List[str]] = []
        phrase_freq = Counter()
        noun_adj = defaultdict(Counter)

        for r in reviews:
            raw = r.text
            cleaned = clean_text(raw)

            # evidence spans
            for sent in split_sentences(cleaned):
                if not sent:
                    continue
                if len(sent) > self.cfg.max_sentence_chars:
                    sent = sent[: self.cfg.max_sentence_chars].strip()
                evidence_spans.append(EvidenceSpan(
                    review_id=r.review_id,
                    sentence=sent,
                    raw_text=raw,
                    rating=r.rating,
                ))

            tokens = tokenize(cleaned)
            phrases: List[str] = []

            if self.cfg.enable_adj_noun:
                for adj, noun in extract_adj_noun_pairs(tokens, self.stopset):
                    phrases.append(f"{adj}_{noun}")
                    noun_adj[noun][adj] += 1

            if self.cfg.enable_noun_phrases:
                phrases.extend(extract_noun_phrases(
                    tokens, self.stopset, max_len=4))

            local = Counter(phrases)
            top_local = [p for p, _ in local.most_common(
                self.cfg.max_phrases_per_review)]
            per_review_docs.append(top_local)
            phrase_freq.update(top_local)

        tfidf_df = tfidf_rank(per_review_docs, self.cfg.min_df)
        if tfidf_df.empty:
            candidates = pd.DataFrame(
                columns=["phrase", "tfidf", "freq", "score"])
        else:
            tfidf_df["freq"] = tfidf_df["phrase"].map(
                lambda p: phrase_freq.get(p, 0)).astype(int)
            tfidf_df["score"] = tfidf_df["tfidf"] * np.log1p(tfidf_df["freq"])
            candidates = tfidf_df.sort_values(
                "score", ascending=False).reset_index(drop=True)

        candidates = candidates.head(self.cfg.top_k_phrases).copy()

        # noun->adjectives signal table (optional)
        rows = []
        for noun, ctr in noun_adj.items():
            total = sum(ctr.values())
            top = ctr.most_common(5)
            rows.append({
                "noun": noun,
                "total_modifiers": total,
                "top_adjectives": ", ".join([f"{a}({c})" for a, c in top]),
            })
        aggregates = pd.DataFrame(rows).sort_values(
            "total_modifiers", ascending=False).reset_index(drop=True)

        return {
            "candidates": candidates,
            "evidence_spans": evidence_spans,
            "aggregates": aggregates,
        }
