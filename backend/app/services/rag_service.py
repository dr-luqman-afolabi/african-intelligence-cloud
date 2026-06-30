"""RAG (Retrieval-Augmented Generation) service.

Uses TF-IDF keyword matching over indicator metadata to retrieve context,
then returns a structured answer. Falls back gracefully if no DB data found.
"""

from __future__ import annotations

import math
import re
import uuid
from collections import Counter
from typing import List

from sqlalchemy.orm import Session

from app.models.indicator import Indicator
from app.models.macro_data import MacroData


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _tfidf_score(query_tokens: List[str], doc_tokens: List[str]) -> float:
    if not doc_tokens:
        return 0.0
    doc_counter = Counter(doc_tokens)
    doc_len = len(doc_tokens)
    score = 0.0
    for t in set(query_tokens):
        tf = doc_counter.get(t, 0) / doc_len
        idf = math.log(1 + 1 / (doc_counter.get(t, 0) + 1))
        score += tf * idf
    return score


def retrieve_context(query: str, db: Session, top_k: int = 5):
    """Return top-k matching indicators and recent data rows."""
    q_tokens = _tokenize(query)
    indicators: List[Indicator] = db.query(Indicator).all()

    scored = []
    for ind in indicators:
        doc = f"{ind.name} {ind.description or ''} {ind.category or ''} {ind.code}"
        score = _tfidf_score(q_tokens, _tokenize(doc))
        if score > 0:
            scored.append((score, ind))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_indicators = scored[:top_k]

    sources = []
    context_chunks = []
    for score, ind in top_indicators:
        rows = (
            db.query(MacroData)
            .filter(MacroData.indicator_code == ind.code)
            .order_by(MacroData.year.desc())
            .limit(3)
            .all()
        )
        excerpt_parts = [f"{ind.name} ({ind.code})"]
        for row in rows:
            excerpt_parts.append(f"  {row.country_iso3} {row.year}: {row.value} {row.unit or ''}")

        excerpt = "\n".join(excerpt_parts)
        context_chunks.append(excerpt)
        sources.append(
            {
                "source_id": ind.code,
                "title": ind.name,
                "score": round(score, 4),
                "excerpt": excerpt[:300],
            }
        )

    return context_chunks, sources


def synthesize_answer(query: str, context_chunks: List[str]) -> str:
    if not context_chunks:
        return (
            f"I could not find specific data in the AIC database for your query: '{query}'. "
            "Try refining your question with specific country names, indicator codes, or years."
        )

    context_text = "\n\n".join(context_chunks)
    return (
        f"Based on AIC data, here is what I found for: **{query}**\n\n"
        f"{context_text}\n\n"
        "_This answer was generated using AIC's data retrieval engine. "
        "Use the Data Explorer for full time-series analysis._"
    )


def answer_query(query: str, db: Session):
    context_chunks, sources = retrieve_context(query, db)
    answer = synthesize_answer(query, context_chunks)
    return {
        "answer": answer,
        "sources": sources,
        "query_id": str(uuid.uuid4()),
    }
