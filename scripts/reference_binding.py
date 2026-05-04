from __future__ import annotations

import re
from typing import Iterable

from reference_models import CitationBinding, ReferenceCandidate, SentenceCandidate


def _sentence_order_key(sentence_id: str) -> tuple[int, int]:
    match = re.match(r"p(\d+)s(\d+)", sentence_id)
    if not match:
        return (10**9, 10**9)
    return (int(match.group(1)), int(match.group(2)))


def _candidate_match_score(sentence: SentenceCandidate, candidate: ReferenceCandidate) -> float:
    sentence_topics = set(str(item) for item in sentence.metadata.get("topicIds", []) if isinstance(item, str))
    candidate_topics = set(candidate.matched_topic_ids)
    topic_overlap = len(sentence_topics & candidate_topics)

    sentence_keywords = set(sentence.keywords)
    candidate_keywords = set(
        str(item)
        for item in candidate.metadata.get("keywords", [])
        if isinstance(item, str)
    )
    keyword_overlap = len(sentence_keywords & candidate_keywords)

    score = topic_overlap * 1.5 + keyword_overlap * 0.25 + sentence.score
    if candidate.verified:
        score += 0.4
    if candidate.user_confirmed:
        score += 0.2
    return score


def bind_references_to_sentences(
    sentences: list[SentenceCandidate],
    candidates: list[ReferenceCandidate],
    *,
    max_adjacent_bindings_per_paragraph: int = 2,
    max_references_per_sentence: int = 1,
) -> list[CitationBinding]:
    sorted_sentences = sorted(sentences, key=lambda item: _sentence_order_key(item.sentence_id))
    paragraph_counts: dict[str, int] = {}
    bindings: list[CitationBinding] = []
    first_appearance_order: dict[str, int] = {}

    for sentence in sorted_sentences:
        paragraph_total = paragraph_counts.get(sentence.paragraph_id, 0)
        if paragraph_total >= max_adjacent_bindings_per_paragraph:
            continue

        ranked_candidates = sorted(
            (
                (candidate, _candidate_match_score(sentence, candidate))
                for candidate in candidates
            ),
            key=lambda item: (-item[1], item[0].candidate_id),
        )

        applied = 0
        for candidate, score in ranked_candidates:
            if applied >= max_references_per_sentence:
                break
            if score < 1.5:
                continue

            if candidate.candidate_id not in first_appearance_order:
                first_appearance_order[candidate.candidate_id] = len(first_appearance_order) + 1

            bindings.append(
                CitationBinding(
                    binding_id=f"{sentence.sentence_id}:{candidate.candidate_id}",
                    sentence_id=sentence.sentence_id,
                    paragraph_id=sentence.paragraph_id,
                    candidate_id=candidate.candidate_id,
                    citation_index=first_appearance_order[candidate.candidate_id],
                    marker=f"[{first_appearance_order[candidate.candidate_id]}]",
                    confidence=round(score, 4),
                    metadata={"sentenceScore": sentence.score},
                )
            )
            paragraph_counts[sentence.paragraph_id] = paragraph_counts.get(sentence.paragraph_id, 0) + 1
            applied += 1

    bindings.sort(key=lambda item: (_sentence_order_key(item.sentence_id), item.citation_index))
    return bindings


def build_ordered_reference_list(
    bindings: Iterable[CitationBinding],
    candidates: list[ReferenceCandidate],
) -> list[ReferenceCandidate]:
    index_by_candidate = {binding.candidate_id: binding.citation_index for binding in bindings}
    used = [candidate for candidate in candidates if candidate.candidate_id in index_by_candidate]
    used.sort(key=lambda item: index_by_candidate[item.candidate_id])
    return used
