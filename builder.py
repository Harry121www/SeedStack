"""Project file creation and build/repair logic for SeedStack."""

import os
import subprocess

from extractors import extract_files, FileEntry, MAX_FILE_PATH_LENGTH
from prompts import MAX_ERROR_CONTEXT, MAX_SOURCE_CONTEXT, MAX_BUILD_LOG


def _collect_source_files(base_dir: str, exts: tuple[str, ...]) -> str:
    result = ""
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'target', '__pycache__')]
        for f in files:
            if f.endswith(exts):
                filepath = os.path.join(root, f)
                relpath = os.path.relpath(filepath, base_dir)
                try:
                    with open(filepath, 'r', encoding='utf-8') as fh:
                        result += f"\n### {relpath}\n```\n{fh.read()}\n```\n"
                except (OSError, UnicodeDecodeError):
                    pass
    return result


def _fix_and_rewrite(error_output: str, base_dir: str, label: str, model) -> bool:
    sources = _collect_source_files(base_dir, ('.vue', '.js', '.json', '.css', '.html', '.java', '.xml', '.yml', '.yaml'))
    prompt = f"""你是全栈专家。下面的{label}项目构建失败，请逐一修复所有错误。

## 构建错误
{error_output[:MAX_ERROR_CONTEXT]}

## 当前源码
{sources[:MAX_SOURCE_CONTEXT]}

请返回所有需要修改的文件。每个文件用 ### N. 相对路径 标记，后跟代码块 ```lang\n完整代码\n```。
只返回修改过的文件，确保修复所有编译错误。"""

    resp = model.invoke(prompt)
    fixed = extract_files(resp.content)
    if not fixed:
        print(f"  [警告] 模型未返回修复文件")
        return False

    for entry in fixed:
        if entry.path.startswith(base_dir):
            full = entry.path
        else:
            full = os.path.join(base_dir, entry.path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, 'w', encoding='utf-8') as f:
            f.write(entry.content)
        print(f"  [修复] {entry.path}")
    return True


def _try_build_frontend(frontend_dir: str, max_attempts: int, model) -> bool:
    for attempt in range(max_attempts):
        print(f"\n  [前端构建] 第{attempt+1}/{max_attempts}次...")

        try:
            r = subprocess.run(
                ["npm", "install"],
                cwd=frontend_dir,
                capture_output=True, text=True,
                timeout=300000
            )
        except FileNotFoundError:
            print("  [跳过] npm 不可用")
            return False
        if r.returncode != 0:
            err = r.stdout[-MAX_BUILD_LOG:] + "\n" + r.stderr[-MAX_BUILD_LOG:]
            print(f"  npm install 失败:\n{err[:MAX_BUILD_LOG]}")
            if attempt < max_attempts - 1:
                print("  → 调用AI修复...")
                _fix_and_rewrite(err, frontend_dir, "Vue前端", model)
                continue
            return False
        print("  npm install 成功")

        try:
            r = subprocess.run(
                ["npx", "vite", "build"],
                cwd=frontend_dir,
                capture_output=True, text=True,
                timeout=300000
            )
        except FileNotFoundError:
            print("  [跳过] npx 不可用")
            return False
        if r.returncode != 0:
            err = r.stdout[-MAX_BUILD_LOG:] + "\n" + r.stderr[-MAX_BUILD_LOG:]
            print(f"  vite build 失败:\n{err[:MAX_BUILD_LOG]}")
            if attempt < max_attempts - 1:
                print("  → 调用AI修复...")
                _fix_and_rewrite(err, frontend_dir, "Vue前端", model)
                continue
            return False
        print("  vite build 成功")
        return True
    return False


def _try_compile_backend(project_dir: str, max_attempts: int, model) -> bool:
    for attempt in range(max_attempts):
        print(f"\n  [后端编译] 第{attempt+1}/{max_attempts}次...")

        try:
            r = subprocess.run(
                ["mvn", "compile", "-q"],
                cwd=project_dir,
                capture_output=True, text=True,
                timeout=600000
            )
        except FileNotFoundError:
            print("  [跳过] Maven 不可用")
            return False
        if r.returncode != 0:
            err = r.stdout[-MAX_BUILD_LOG:] + "\n" + r.stderr[-MAX_BUILD_LOG:]
            print(f"  mvn compile 失败:\n{err[:MAX_BUILD_LOG]}")
            if attempt < max_attempts - 1:
                print("  → 调用AI修复...")
                _fix_and_rewrite(err, project_dir, "Spring Boot后端", model)
                continue
            return False
        print("  mvn compile 成功")
        return True
    return False


def create_project(state: dict) -> dict:
    project_dir = os.path.abspath("huini_barter")
    frontend_dir = os.path.join(project_dir, "frontend")

    all_code = "\n".join(state["code_parts"])
    raw_files = extract_files(all_code)

    files: list[FileEntry] = []
    for entry in raw_files:
        path = entry.path.strip()
        if "\n" in path or "\r" in path:
            print(f"  [跳过] 路径包含换行: {path[:80]}...")
            continue
        if len(path) > MAX_FILE_PATH_LENGTH:
            print(f"  [跳过] 路径过长({len(path)}): {path[:80]}...")
            continue
        if not entry.content.strip():
            print(f"  [跳过] 空内容: {path}")
            continue
        files.append(entry)

    backend_count = 0
    frontend_count = 0
    for entry in files:
        if entry.path.startswith("frontend/"):
            full_path = os.path.join(project_dir, entry.path)
            frontend_count += 1
        else:
            full_path = os.path.join(project_dir, entry.path)
            backend_count += 1
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(entry.content)
        except OSError as e:
            print(f"  [错误] 写入失败 {entry.path}: {e}")

    print("[7/8] 创建项目: 后端%d个 + 前端%d个 = %d个文件" % (backend_count, frontend_count, len(files)))

    docs_dir = os.path.join(project_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, "需求文档.md"), "w", encoding="utf-8") as f:
        f.write(state["requirement_doc"])
    with open(os.path.join(docs_dir, "API文档.md"), "w", encoding="utf-8") as f:
        f.write(state["api_doc"])

    with open(os.path.join(project_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("""# 汇尼易链 - 点对点免费易货平台

## 技术栈
- 后端: Java 17 + Spring Boot 3.2 + Spring Data JPA + Spring Security + JWT + Lombok
- 数据库: MySQL 8.0
- 前端: Vue 3 + Vite + Vue Router 4 + Pinia + Axios
- 构建: Maven (后端) + Vite (前端)

## 快速启动

### 1. 创建数据库
```sql
CREATE DATABASE huini_barter CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 修改 application.yml 中的MySQL用户名密码

### 3. 启动后端
```bash
cd huini_barter
mvn spring-boot:run
```
后端: http://localhost:8080

### 4. 启动前端
```bash
cd huini_barter/frontend
npm install
npm run dev
```
前端: http://localhost:5173

## 默认账号
| 角色 | 账号 | 密码 |
|------|------|------|
| 管理员 | admin | 123456 |
| 测试用户 | 13800000001 | 123456 |
| 测试用户 | 13800000002 | 123456 |
| 测试用户 | 13800000003 | 123456 |

## 核心功能
- 点对点免费易货（零佣金零手续费）
- 8大品类覆盖（五金建材/日用百货/餐饮服务/车辆房产/企业库存/数码家电/本地生活）
- 寄卖专区独立模块（成交仅收5%服务费）
- 同城/区域货品筛选
- 商家免费入驻（资质审核）
- 平台担保交易存证
- 总部后台统一管理（审核/公告/统计）

## 设计原则
- 去层级、去代理、无分润入口
- 移动端优先、大字体大按钮、中老年友好
- 底部5栏固定导航（首页/易货广场/发布/寄卖商城/我的）
""")

    print("  + docs/需求文档.md")
    print("  + docs/API文档.md")
    print("  + README.md")
    print("\n项目路径: %s" % project_dir)
    return {"project_dir": project_dir, "frontend_dir": frontend_dir}


def auto_build_fix(state: dict, model) -> dict:
    frontend_dir = state.get("frontend_dir", "")
    project_dir = state.get("project_dir", "")
    max_attempts = 3

    print("\n" + "=" * 60)
    print("[8/8] 自动构建与修复")

    if frontend_dir and os.path.isdir(frontend_dir):
        try:
            node_ok = subprocess.run(["node", "--version"], capture_output=True, text=True)
        except FileNotFoundError:
            node_ok = None
        if node_ok is None or node_ok.returncode != 0:
            print("  [跳过] Node.js 未安装，跳过前端构建检查")
        else:
            print(f"  Node.js {node_ok.stdout.strip()}")
            fe_built = _try_build_frontend(frontend_dir, max_attempts, model)
            if fe_built:
                print("  [前端] 构建成功!")
            else:
                print("  [前端] 构建仍有问题，请手动检查")

    if project_dir and os.path.isdir(project_dir):
        try:
            mvn_ok = subprocess.run(["mvn", "--version"], capture_output=True, text=True)
        except FileNotFoundError:
            mvn_ok = None
        if mvn_ok is None or mvn_ok.returncode != 0:
            print("  [跳过] Maven 未安装，跳过后端编译检查")
        else:
            print(f"  Maven 可用")
            be_built = _try_compile_backend(project_dir, max_attempts, model)
            if be_built:
                print("  [后端] 编译成功!")
            else:
                print("  [后端] 编译仍有问题，请手动检查")

    print("=" * 60)
    return {}
