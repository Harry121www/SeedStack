# SeedStack Code Quality Refactoring Design

**Date**: 2026-05-18
**Status**: Approved

## Goal

Refactor the single-file 817-line `main.py` into a modular 6-file structure, fix 5 categories of code quality issues identified in the evaluation report.

## New File Structure

```
F:\Agent\Test\
├── main.py              # Entry point + CLI (~30 lines)
├── workflow.py           # LangGraph workflow assembly (~50 lines)
├── generators.py         # 8 gen_* functions (~350 lines)
├── extractors.py         # File extraction, strategy pattern (~120 lines)
├── prompts.py            # All prompt templates (~200 lines)
├── builder.py            # Project creation + build/repair (~180 lines)
```

## Module Design

### extractors.py
- Exports `FileEntry` dataclass (path, content) to replace bare tuples
- Exports `extract_files(text)` — main function using strategy list
- 11 strategies as private functions, each signature: `(text: str) -> list[FileEntry] | None`
- Exports `dump_debug(content, step_name)` — deduplicated debug dump
- Constants: `MAX_FILE_PATH_LENGTH = 200`, `MIN_FILES_THRESHOLD = 2`

### prompts.py
- 11 prompt template constants (uppercase): `DOCS_PROMPT`, `BACKEND_INFRA_PROMPT`, etc.
- Exports `fill(template, **kwargs)` — placeholder substitution from old main.py

### generators.py
- 8 step functions: `generate_docs`, `gen_backend_infra`, `gen_backend_domain`, `gen_services`, `gen_controllers`, `gen_vue_config_components`, `gen_vue_views`, `create_project`
- Signature: `(state: WorkflowState, model) -> dict`
- `model` is injected, not accessed from global scope

### builder.py
- `create_project(state) -> dict`
- `auto_build_fix(state) -> dict`
- `_try_build_frontend(dir, max_attempts, model) -> bool`
- `_try_compile_backend(dir, max_attempts, model) -> bool`
- `_fix_and_rewrite(error_output, base_dir, label, model) -> bool`
- `_collect_source_files(base_dir, exts) -> str`

### workflow.py
- Imports `WorkflowState` from main (or shared types)
- `build_agent(draft_mode: bool, model)` — assembles StateGraph, returns compiled agent

### main.py
- Model initialization: `model = init_chat_model(...)`
- `WorkflowState` TypedDict
- `agent = build_agent(draft_mode=False, model=model)`
- `main()` CLI entry point

## Specific Fixes

1. **Bare except** — `except:` → `except (OSError, UnicodeDecodeError):`
2. **Magic numbers** — named constants: `MAX_PROMPT_CONTEXT=2000`, `MAX_ERROR_CONTEXT=3000`, `MAX_SOURCE_CONTEXT=12000`, `MAX_BUILD_LOG=1500`
3. **Variable naming** — `fs`→`files`, `rd`→`requirement_doc`, `ad`→`api_doc`, `c`→`content`, `tpl`→`template`, `be_count`→`backend_count`, `fe_count`→`frontend_count`
4. **Debug dump dedup** — 4 repeated blocks → single `dump_debug()` in extractors.py
5. **extract_files refactor** — strategy list pattern instead of chained if/return

## What Does NOT Change

- LangGraph workflow logic and step order
- Prompt content
- LLM model choice and configuration
- pyproject.toml dependencies (except removing unused `langchain-anthropic`)
- CLI interface (`--draft` flag, requirement file input)
