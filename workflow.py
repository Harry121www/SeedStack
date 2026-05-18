"""LangGraph workflow assembly for SeedStack."""

from langgraph.graph import StateGraph, START, END

from generators import (
    generate_docs,
    gen_backend_infra,
    gen_backend_domain,
    gen_services,
    gen_controllers,
    gen_vue_config_components,
    gen_vue_views,
)
from builder import create_project, auto_build_fix


def build_agent(draft_mode: bool = False, model=None):
    all_steps = [
        ("docs",                  generate_docs),
        ("backend_infra",         gen_backend_infra),
        ("backend_domain",        gen_backend_domain),
        ("services",              gen_services),
        ("controllers",           gen_controllers),
        ("vue_config_components", gen_vue_config_components),
        ("vue_views",             gen_vue_views),
        ("create_project",        create_project),
    ]
    if not draft_mode:
        all_steps.append(("auto_build_fix", auto_build_fix))

    wf = StateGraph(dict)
    for name, fn in all_steps:
        # Wrap LLM-based steps to inject model
        if fn in (generate_docs, gen_backend_infra, gen_backend_domain,
                  gen_services, gen_controllers, gen_vue_config_components,
                  gen_vue_views):
            original = fn
            fn = lambda state, f=original: f(state, model)

        if fn == auto_build_fix:
            original = fn
            fn = lambda state, f=original: f(state, model)

        wf.add_node(name, fn)

    prev = START
    for name, _ in all_steps:
        wf.add_edge(prev, name)
        prev = name
    wf.add_edge(all_steps[-1][0], END)
    return wf.compile()
