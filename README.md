# AI 全栈代码生成器

输入一句需求描述，自动生成完整的全栈项目代码（Spring Boot 后端 + Vue 3 前端），并尝试编译修复。

## 工作流程（8 步）

1. **文档生成** — 根据需求生成需求文档和 API 接口文档
2. **后端基础设施** — pom.xml / application.yml / 建表 SQL / Security + JWT 配置
3. **领域层** — Entity、Enum、Repository、DTO（约 37 个文件）
4. **Service 层** — 11 个业务 Service（认证、用户、商品、订单、寄卖等）
5. **Controller 层** — 12 个 REST Controller + 数据初始化器
6. **前端配置组件** — Vite 配置、路由、Store、公共组件（12 个文件）
7. **前端视图页面** — 16 个页面（首页、易货广场、寄卖商城、个人中心等）
8. **自动构建修复** — npm install + vite build / mvn compile，失败时调 AI 自动修复（最多 3 轮）

## 技术栈

- **编排**: LangGraph（StateGraph 工作流）
- **LLM**: DeepSeek（通过 LangChain 调用）
- **后端生成**: Spring Boot 3.2 + JPA + Security + JWT + MySQL
- **前端生成**: Vue 3 + Vite + Pinia + Vue Router + Axios
- **构建**: Maven（后端）+ Vite（前端）

## 快速开始

```bash
# 安装依赖
uv sync

# 配置 API Key（.env 文件）
# DEEPSEEK_API_KEY=your_key_here

# 运行
uv run python main.py                    # 交互式输入需求
uv run python main.py requirement.txt    # 从文件读取需求
uv run python main.py --draft            # 跳过自动构建修复（仅生成代码）
```

## 示例输出

生成的完整项目在 `huini_barter/` 目录下，可以直接用 IDE 打开编译运行。

## 依赖

- Python >= 3.11
- Node.js（前端构建需要）
- Maven + JDK 17（后端编译需要）
