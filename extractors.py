"""File extraction strategies and debug utilities for SeedStack."""

import re
import os
from dataclasses import dataclass

MAX_FILE_PATH_LENGTH = 200
MIN_FILES_THRESHOLD = 2


@dataclass
class FileEntry:
    path: str
    content: str


def _strategy_file_markers(text: str) -> list[FileEntry] | None:
    p = r'###FILE:\s*(.+?)\s*###\s*\n(.*?)###END###'
    m = re.findall(p, text, re.DOTALL)
    if m and len(m) >= MIN_FILES_THRESHOLD:
        return [FileEntry(x[0].strip(), x[1].strip()) for x in m]
    return None


def _strategy_file_with_code(text: str) -> list[FileEntry] | None:
    p = r'###FILE:\s*(.+?)\s*###\s*\n```\w*\s*\n(.*?)```'
    m = re.findall(p, text, re.DOTALL)
    if m and len(m) >= MIN_FILES_THRESHOLD:
        return [FileEntry(x[0].strip(), x[1].strip()) for x in m]
    return None


def _strategy_numbered_path(text: str) -> list[FileEntry] | None:
    p = r'###\s*\d+\.\s*(.+?\.\w+)\s*\n\s*```\w*\s*\n(.*?)```'
    m = re.findall(p, text, re.DOTALL)
    if m and len(m) >= MIN_FILES_THRESHOLD:
        return [FileEntry(x[0].strip(), x[1].strip()) for x in m]
    return None


def _strategy_bold_path(text: str) -> list[FileEntry] | None:
    p = r'\*\*(.+?\.\w+)\*\*\s*\n\s*```\w*\s*\n(.*?)```'
    m = re.findall(p, text, re.DOTALL)
    if m and len(m) >= MIN_FILES_THRESHOLD:
        return [FileEntry(x[0].strip(), x[1].strip()) for x in m]
    return None


def _strategy_filepath_block(text: str) -> list[FileEntry] | None:
    p = r'```filepath\s*\n(.+?)\n```\w*\s*\n(.*?)```'
    m = re.findall(p, text, re.DOTALL)
    if m:
        return [FileEntry(x[0].strip(), x[1].strip()) for x in m]
    return None


def _strategy_path_code_block(text: str) -> list[FileEntry] | None:
    p = r'```([\w./-]+/[\w./-]+\.\w+)\s*\n(.*?)```'
    m = re.findall(p, text, re.DOTALL)
    if m and len(m) >= MIN_FILES_THRESHOLD:
        return [FileEntry(x[0].strip(), x[1].strip()) for x in m]
    return None


def _strategy_loose_numbered(text: str) -> list[FileEntry] | None:
    p = r'(?:^|\n)\s*\d+\.\s*([\w./-]+\.\w+)\s*\n\s*```\w*\s*\n(.*?)```'
    m = re.findall(p, text, re.DOTALL)
    if m and len(m) >= MIN_FILES_THRESHOLD:
        return [FileEntry(x[0].strip(), x[1].strip()) for x in m]
    return None


def _strategy_markdown_heading(text: str) -> list[FileEntry] | None:
    p = r'##\s*\d+\.\s*([\w./-]+\.\w+)\s*\n\s*```\w*\s*\n(.*?)```'
    m = re.findall(p, text, re.DOTALL)
    if m and len(m) >= MIN_FILES_THRESHOLD:
        return [FileEntry(x[0].strip(), x[1].strip()) for x in m]
    return None


def _strategy_json_format(text: str) -> list[FileEntry] | None:
    p = r'"path"\s*:\s*"([^"]+)"\s*,\s*"(?:language|lang)"\s*:\s*"[^"]*"\s*,\s*"content"\s*:\s*"((?:[^"\\]|\\.)*)"'
    m = re.findall(p, text)
    if m and len(m) >= MIN_FILES_THRESHOLD:
        result = []
        for filepath, content in m:
            content = content.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
            result.append(FileEntry(filepath.strip(), content.strip()))
        return result
    return None


def _strategy_backtick_path(text: str) -> list[FileEntry] | None:
    p = r'###\s*\d+\.\s*`([^`]+)`\s*\n\s*```\w*\s*\n(.*?)```'
    m = re.findall(p, text, re.DOTALL)
    if m and len(m) >= MIN_FILES_THRESHOLD:
        return [FileEntry(x[0].strip(), x[1].strip()) for x in m]
    return None


def _strategy_markers_in_code(text: str) -> list[FileEntry] | None:
    p_marker = r'^##\s*\d+\.\s*([\w./-]+\.\w+)\s*$'
    lines = text.split('\n')
    found = []
    for i, line in enumerate(lines):
        m = re.match(p_marker, line)
        if m:
            found.append((i, m.group(1).strip()))
    if len(found) < MIN_FILES_THRESHOLD:
        return None
    result = []
    for j, (line_idx, filepath) in enumerate(found):
        start = line_idx + 1
        end = found[j + 1][0] if j + 1 < len(found) else len(lines)
        code = '\n'.join(lines[start:end]).strip()
        code = re.sub(r'^```\w*\s*', '', code)
        code = re.sub(r'\s*```\s*$', '', code)
        if code:
            result.append(FileEntry(filepath, code))
    return result


STRATEGIES = [
    _strategy_file_markers,
    _strategy_file_with_code,
    _strategy_numbered_path,
    _strategy_bold_path,
    _strategy_filepath_block,
    _strategy_path_code_block,
    _strategy_loose_numbered,
    _strategy_markdown_heading,
    _strategy_json_format,
    _strategy_backtick_path,
    _strategy_markers_in_code,
]


def extract_files(text: str) -> list[FileEntry]:
    """Extract file entries from LLM response using multiple strategies."""
    for strategy in STRATEGIES:
        result = strategy(text)
        if result and len(result) >= MIN_FILES_THRESHOLD:
            return result
    return []


def dump_debug(content: str, step_name: str) -> str:
    """Save LLM response to a debug file when no files were extracted."""
    debug_dir = os.path.dirname(__file__) if '__file__' in dir() else os.getcwd()
    debug_path = os.path.join(debug_dir, f"debug_{step_name}_response.txt")
    with open(debug_path, "w", encoding="utf-8") as f:
        f.write(content[:3000])
    return debug_path
