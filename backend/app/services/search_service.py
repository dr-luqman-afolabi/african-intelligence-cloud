"""Semantic search service — TF-IDF keyword search over indicators and catalog."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import List

from sqlalchemy.orm import Session

from app.models.indicator import Indicator
from app.models.macro_data import MacroData


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _score(query_tokens: List[str], doc: str) -> float:
    doc_tokens = _tokenize(doc)
    if not doc_tokens:
        return 0.0
    doc_counter = Counter(doc_tokens)
    doc_len = len(doc_tokens)
    s = 0.0
    for t in set(query_tokens):
        tf = doc_counter.get(t, 0) / doc_len
        idf = math.log(1 + 10 / (doc_counter.get(t, 0) + 1))
        s += tf * idf
    return s


def semantic_search(query: str, db: Session, limit: int = 10) -> List[dict]:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    indicators: List[Indicator] = db.query(Indicator).all()

    results = []
    seen_codes: set = set()
    for ind in indicators:
        doc = f"{ind.name} {ind.description or ''} {ind.category or ''} {ind.source or ''} {ind.code}"
        score = _score(q_tokens, doc)
        if score <= 0:
            continue
        if ind.code in seen_codes:
            continue
        seen_codes.add(ind.code)

        row_count = (
            db.query(MacroData)
            .filter(MacroData.indicator_code == ind.code)
            .count()
        )

        results.append(
            {
                "dataset_id": ind.code,
                "title": ind.name,
                "description": ind.description or "",
                "score": round(score, 4),
                "source_id": ind.source or "aic",
                "tags": [ind.category or "general", ind.unit or ""],
                "record_count": row_count,
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
