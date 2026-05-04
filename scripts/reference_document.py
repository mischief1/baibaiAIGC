from __future__ import annotations

import re
from pathlib import Path

from docx_pipeline import read_docx_paragraphs
from reference_models import ParagraphNode, ReferenceDocument, SentenceNode


REFERENCE_SECTION_MARKERS = {
    "参考文献",
    "参考文献列表",
    "references",
    "bibliography",
}

HEADING_PATTERNS = (
    re.compile(r"^第[一二三四五六七八九十百0-9]+[章节部分篇]\s*.*$"),
    re.compile(r"^[0-9]+(\.[0-9]+)*\s+\S+$"),
    re.compile(r"^[一二三四五六七八九十]+[、.．]\s*\S+$"),
)

SENTENCE_SPLIT_PATTERN = re.compile(r"(.+?[。！？!?；;])")


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def split_text_to_paragraphs(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    paragraphs: list[str] = []
    current: list[str] = []
    for raw_line in normalized.split("\n"):
        line = raw_line.strip()
        if not line:
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current).strip())
    return paragraphs


def is_heading(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if len(stripped) <= 30 and not re.search(r"[。！？!?；;]$", stripped):
        if any(pattern.match(stripped) for pattern in HEADING_PATTERNS):
            return True
        if len(stripped.split()) <= 6 and stripped.endswith(("摘要", "引言", "绪论", "结论")):
            return True
        if stripped in {"摘要", "引言", "绪论", "结论", "讨论", "方法", "结果"}:
            return True
    return False


def is_reference_section_heading(text: str) -> bool:
    compact = re.sub(r"\s+", "", text).strip().lower()
    return compact in REFERENCE_SECTION_MARKERS


def split_paragraph_to_sentences(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []

    sentences: list[str] = []
    cursor = 0
    for match in SENTENCE_SPLIT_PATTERN.finditer(stripped):
        sentence = match.group(1).strip()
        if sentence:
            sentences.append(sentence)
        cursor = match.end()

    remainder = stripped[cursor:].strip()
    if remainder:
        sentences.append(remainder)

    if not sentences:
        sentences.append(stripped)
    return sentences


def _build_paragraph_nodes(paragraph_texts: list[str]) -> list[ParagraphNode]:
    paragraphs: list[ParagraphNode] = []
    current_section_title = ""

    for paragraph_index, paragraph_text in enumerate(paragraph_texts):
        if is_reference_section_heading(paragraph_text):
            break

        heading = is_heading(paragraph_text)
        if heading:
            current_section_title = paragraph_text.strip()

        sentence_texts = split_paragraph_to_sentences(paragraph_text)
        sentences = [
            SentenceNode(
                sentence_id=f"p{paragraph_index}s{sentence_index}",
                paragraph_id=f"p{paragraph_index}",
                text=sentence_text,
                order=sentence_index,
                section_title=current_section_title,
                has_citation=bool(re.search(r"\[[0-9]+\]", sentence_text)),
            )
            for sentence_index, sentence_text in enumerate(sentence_texts)
        ]
        paragraphs.append(
            ParagraphNode(
                paragraph_id=f"p{paragraph_index}",
                text=paragraph_text,
                order=paragraph_index,
                section_title=current_section_title,
                sentences=sentences,
                metadata={"isHeading": heading},
            )
        )
    return paragraphs


def parse_reference_document(path: str | Path) -> ReferenceDocument:
    source_path = Path(path)
    suffix = source_path.suffix.lower()
    if suffix == ".docx":
        paragraph_texts = read_docx_paragraphs(source_path)
        file_type = "docx"
    else:
        paragraph_texts = split_text_to_paragraphs(source_path.read_text(encoding="utf-8"))
        file_type = suffix.lstrip(".") or "txt"

    paragraphs = _build_paragraph_nodes(paragraph_texts)
    sentence_count = sum(len(paragraph.sentences) for paragraph in paragraphs)
    title = paragraphs[0].text if paragraphs else source_path.stem

    return ReferenceDocument(
        source_path=str(source_path),
        file_type=file_type,
        title=title,
        paragraphs=paragraphs,
        sentence_count=sentence_count,
        metadata={"excludedReferenceSection": len(paragraphs) < len(paragraph_texts)},
    )
