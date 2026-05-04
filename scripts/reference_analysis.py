from __future__ import annotations

import math
import re
from collections import Counter

from reference_models import ReferenceDocument, SentenceCandidate, TopicCluster


SECTION_BOOSTS = {
    "文献综述": 0.35,
    "研究背景": 0.25,
    "研究方法": 0.15,
    "理论基础": 0.2,
    "引言": 0.05,
}

PHRASE_BOOSTS = {
    "已有研究表明": 0.45,
    "研究表明": 0.35,
    "学者认为": 0.3,
    "普遍认为": 0.3,
    "根据": 0.2,
    "制度理论": 0.35,
    "理论": 0.15,
    "表明": 0.15,
}

LOW_VALUE_PHRASES = (
    "本文首先",
    "文章结构",
    "下文安排",
    "本研究分为",
)


def _extract_section_boost(section_title: str) -> float:
    for keyword, boost in SECTION_BOOSTS.items():
        if keyword and keyword in section_title:
            return boost
    return 0.0


def _extract_keywords(text: str) -> list[str]:
    normalized = re.sub(r"[，。！？；、,.!?;:\s]+", "", text)
    normalized = re.sub(r"(已有研究表明|研究表明|学者普遍认为|学者认为|普遍认为|根据|本文|本研究)", "", normalized)
    chinese_runs = re.findall(r"[\u4e00-\u9fff]{2,}", normalized)
    english_words = [word.lower() for word in re.findall(r"[A-Za-z]{4,}", text)]

    keywords: list[str] = []
    for run in chinese_runs:
        if len(run) <= 4:
            keywords.append(run)
            continue
        for index in range(len(run) - 1):
            token = run[index:index + 2]
            if token not in keywords:
                keywords.append(token)

    for word in english_words:
        if word not in keywords:
            keywords.append(word)
    return keywords[:12]


def score_sentence_candidates(document: ReferenceDocument, *, limit: int = 60) -> list[SentenceCandidate]:
    candidates: list[SentenceCandidate] = []

    for paragraph in document.paragraphs:
        for sentence in paragraph.sentences:
            if sentence.has_citation:
                continue

            text = sentence.text.strip()
            if not text:
                continue

            score = 0.05 + _extract_section_boost(sentence.section_title)
            matched_signals: list[str] = []

            for phrase, boost in PHRASE_BOOSTS.items():
                if phrase in text:
                    score += boost
                    matched_signals.append(phrase)

            for phrase in LOW_VALUE_PHRASES:
                if phrase in text:
                    score -= 0.2
                    matched_signals.append(f"low:{phrase}")

            if re.search(r"\d{4}", text):
                score += 0.05
                matched_signals.append("year")

            score = max(0.0, min(score, 1.0))
            keywords = _extract_keywords(text)
            candidates.append(
                SentenceCandidate(
                    sentence_id=sentence.sentence_id,
                    text=text,
                    score=round(score, 4),
                    paragraph_id=sentence.paragraph_id,
                    section_title=sentence.section_title,
                    matched_signals=matched_signals,
                    keywords=keywords,
                    metadata={"isHeading": bool(paragraph.metadata.get("isHeading"))},
                )
            )

    candidates.sort(key=lambda item: (-item.score, item.sentence_id))
    return candidates[:limit]


def _jaccard_overlap(left: list[str], right: list[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def build_topic_clusters(candidates: list[SentenceCandidate], *, max_clusters: int = 20) -> list[TopicCluster]:
    clusters: list[TopicCluster] = []

    for candidate in candidates:
        matched_cluster: TopicCluster | None = None
        for cluster in clusters:
            overlap = _jaccard_overlap(candidate.keywords, cluster.keywords)
            if overlap >= 0.18:
                matched_cluster = cluster
                break

        if matched_cluster is None:
            if len(clusters) >= max_clusters:
                continue
            label_tokens = candidate.keywords[:3] if candidate.keywords else [candidate.text[:8]]
            cluster = TopicCluster(
                topic_id=f"topic-{len(clusters) + 1}",
                label=" / ".join(label_tokens[:2]),
                query=" ".join(label_tokens[:3]),
                sentence_ids=[candidate.sentence_id],
                keywords=list(candidate.keywords),
                summary=candidate.text,
                metadata={"scoreTotal": candidate.score},
            )
            clusters.append(cluster)
            continue

        matched_cluster.sentence_ids.append(candidate.sentence_id)
        combined = list(dict.fromkeys(matched_cluster.keywords + candidate.keywords))
        matched_cluster.keywords = combined[:12]
        matched_cluster.metadata["scoreTotal"] = round(
            float(matched_cluster.metadata.get("scoreTotal", 0.0)) + candidate.score,
            4,
        )

    clusters.sort(
        key=lambda item: (
            -len(item.sentence_ids),
            -float(item.metadata.get("scoreTotal", 0.0)),
            item.topic_id,
        )
    )
    return clusters


def recommend_reference_counts(
    document: ReferenceDocument,
    clusters: list[TopicCluster],
    *,
    candidate_count: int,
) -> dict[str, int]:
    sentence_factor = max(1, math.ceil(document.sentence_count / 8))
    cluster_factor = max(1, len(clusters) * 2)
    candidate_factor = max(1, math.ceil(candidate_count * 1.5))
    recommended_total = max(6, min(60, sentence_factor + cluster_factor + candidate_factor))

    if recommended_total <= 6:
        chinese_count = 2
    else:
        chinese_count = max(2, round(recommended_total * 0.4))
    english_count = max(2, recommended_total - chinese_count)

    if chinese_count + english_count < recommended_total:
        english_count += recommended_total - chinese_count - english_count

    return {
        "recommendedTotalCount": recommended_total,
        "recommendedChineseCount": chinese_count,
        "recommendedEnglishCount": english_count,
        "recommendedCitationPositionsCount": candidate_count,
    }
