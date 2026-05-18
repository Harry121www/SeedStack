"""SeedStack — AI-powered full-stack code generator.

Input a requirement description, output a complete Spring Boot + Vue 3 project.
"""

import sys

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from workflow import build_agent

load_dotenv()
model = init_chat_model("deepseek-chat", max_tokens=8192)

# Module-level default agent (full mode)
agent = build_agent(draft_mode=False, model=model)


def main():
    draft_mode = "--draft" in sys.argv

    print("=" * 60)
    mode_desc = "7步草稿模式 (跳过自动修复)" if draft_mode else "8步完整模式"
    print("多Agent工作流 v8 (%s)" % mode_desc)
    print("=" * 60)

    requirement = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            with open(arg, "r", encoding="utf-8") as f:
                requirement = f.read()
            print("需求文件: %s\n" % arg)
            break

    if requirement is None:
        requirement = input("请输入项目需求:\n")

    if draft_mode:
        draft_agent = build_agent(draft_mode=True, model=model)
        result = draft_agent.invoke({"requirement": requirement})
    else:
        result = agent.invoke({"requirement": requirement})

    print("\n生成完毕: %s" % result.get("project_dir", "未知"))
    if draft_mode:
        print("提示: 用 Claude Code 对话说\"审校 hairpro_spring\"来调用 superpowers 做深度 review")


if __name__ == "__main__":
    main()
