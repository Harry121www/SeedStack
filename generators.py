"""LLM generation step functions for SeedStack workflow."""

from extractors import extract_files, dump_debug
from prompts import (
    fill,
    MAX_PROMPT_CONTEXT,
    DOCS_PROMPT,
    BACKEND_INFRA_PROMPT,
    BACKEND_DOMAIN_PROMPT,
    SERVICES_PROMPT,
    CONTROLLERS_PROMPT,
    VUE_CONFIG_PROMPT,
    VUE_VIEWS_PROMPT,
    MAX_REQ_DOC_BRIEF,
    MAX_REQ_DOC_TINY,
)


def generate_docs(state: dict, model) -> dict:
    resp = model.invoke(fill(DOCS_PROMPT, REQUIREMENT=state["requirement"]))
    content = resp.content
    requirement_doc, api_doc = "", ""
    if "---需求文档---" in content and "---API接口文档---" in content:
        parts = content.split("---需求文档---")[1]
        if "---API接口文档---" in parts:
            requirement_doc = parts.split("---API接口文档---")[0].strip()
            api_doc = parts.split("---API接口文档---")[1].strip()
    else:
        requirement_doc = api_doc = content
    print("[1/8] 文档完成 (需求%d字, API%d字)" % (len(requirement_doc), len(api_doc)))
    return {"requirement_doc": requirement_doc, "api_doc": api_doc, "code_parts": []}


def gen_backend_infra(state: dict, model) -> dict:
    print("[2/8] 后端基础设施 (pom/sql/config/security)...")
    resp = model.invoke(fill(BACKEND_INFRA_PROMPT, REQ_DOC=state["requirement_doc"][:MAX_PROMPT_CONTEXT]))
    files = extract_files(resp.content)
    print("  %d个: %s" % (len(files), [f.path for f in files]))
    return {"code_parts": state["code_parts"] + [resp.content]}


def gen_backend_domain(state: dict, model) -> dict:
    print("[3/8] 实体/枚举/仓库/DTO (37个)...")
    resp = model.invoke(fill(BACKEND_DOMAIN_PROMPT, API_DOC=state["api_doc"][:MAX_PROMPT_CONTEXT]))
    files = extract_files(resp.content)
    print("  %d个: %s" % (len(files), [f.path for f in files]))
    return {"code_parts": state["code_parts"] + [resp.content]}


def gen_services(state: dict, model) -> dict:
    print("[4/8] Service层 (11个)...")
    resp = model.invoke(fill(SERVICES_PROMPT, API_DOC=state["api_doc"][:MAX_PROMPT_CONTEXT]))
    files = extract_files(resp.content)
    if len(files) == 0:
        debug_path = dump_debug(resp.content, "step4")
        print(f"  [调试] 0个文件, 保存到 {debug_path}")
    print("  %d个: %s" % (len(files), [f.path for f in files]))
    return {"code_parts": state["code_parts"] + [resp.content]}


def gen_controllers(state: dict, model) -> dict:
    print("[5/8] Controller + 数据初始化 (13个)...")
    resp = model.invoke(fill(CONTROLLERS_PROMPT, API_DOC=state["api_doc"][:MAX_PROMPT_CONTEXT]))
    files = extract_files(resp.content)
    if len(files) == 0:
        debug_path = dump_debug(resp.content, "step5")
        print(f"  [调试] 0个文件, 保存到 {debug_path}")
    print("  %d个: %s" % (len(files), [f.path for f in files]))
    return {"code_parts": state["code_parts"] + [resp.content]}


def gen_vue_config_components(state: dict, model) -> dict:
    print("[6a/8] Vue前端-配置组件 (12个)...")
    resp = model.invoke(fill(VUE_CONFIG_PROMPT, REQ_DOC=state["requirement_doc"][:MAX_REQ_DOC_BRIEF]))
    files = extract_files(resp.content)
    if len(files) == 0:
        debug_path = dump_debug(resp.content, "vue_part1")
        print(f"  [调试] 0个文件, 保存到 {debug_path}")
    print("  %d个: %s" % (len(files), [f.path for f in files]))
    return {"code_parts": state["code_parts"] + [resp.content]}


def gen_vue_views(state: dict, model) -> dict:
    print("[6b/8] Vue前端-视图页面 (16个)...")
    resp = model.invoke(fill(VUE_VIEWS_PROMPT, REQUIREMENT=state["requirement_doc"][:MAX_REQ_DOC_TINY]))
    files = extract_files(resp.content)
    if len(files) == 0:
        debug_path = dump_debug(resp.content, "vue_part2")
        print(f"  [调试] 0个文件, 保存到 {debug_path}")
    print("  %d个: %s" % (len(files), [f.path for f in files]))
    return {"code_parts": state["code_parts"] + [resp.content]}
