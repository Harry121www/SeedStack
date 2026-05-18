# SeedStack Code Quality Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor 817-line single-file `main.py` into 6 focused modules, fixing all 5 categories of code quality issues identified in the evaluation.

**Architecture:** Extract modules by responsibility — file extraction, prompt templates, LLM generation, project building, workflow assembly, CLI entry. Model is injected as a parameter to all functions that need it. `FileEntry` dataclass replaces bare tuples.

**Tech Stack:** Python 3.11, LangChain, LangGraph, DeepSeek (unchanged)

---

### Task 1: Create `extractors.py`

**Files:**
- Create: `F:\Agent\Test\extractors.py`

- [ ] **Step 1: Write extractors.py**

```python
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
```

- [ ] **Step 2: Verify syntax**

```bash
uv run python -c "from extractors import FileEntry, extract_files, dump_debug, STRATEGIES; print(f'{len(STRATEGIES)} strategies loaded, FileEntry={FileEntry}')"
```

Expected: `11 strategies loaded, FileEntry=<class 'extractors.FileEntry'>`

- [ ] **Step 3: Commit**

```bash
git add F:\Agent\Test\extractors.py
git commit -m "refactor: extract file parsing strategies to extractors.py"
```

---

### Task 2: Create `prompts.py`

**Files:**
- Create: `F:\Agent\Test\prompts.py`

- [ ] **Step 1: Write prompts.py**

```python
"""Prompt templates and placeholder substitution for SeedStack."""

MAX_PROMPT_CONTEXT = 2000
MAX_ERROR_CONTEXT = 3000
MAX_SOURCE_CONTEXT = 12000
MAX_BUILD_LOG = 1500
MAX_REQ_DOC_BRIEF = 1000
MAX_REQ_DOC_TINY = 500


def fill(template: str, **kw: str) -> str:
    """Replace __KEY__ placeholders in template with values."""
    for k, v in kw.items():
        template = template.replace("__" + k + "__", v)
    return template


DOCS_PROMPT = """你是一个资深的产品经理和技术架构师。根据以下需求生成两份文档。

## 项目需求
__REQUIREMENT__

请严格用以下分隔线输出：

---需求文档---
（项目概述、功能模块详情、非功能需求、用户故事等）

---API接口文档---
（RESTful API 设计：数据模型、接口列表、请求/响应格式）
"""

BACKEND_INFRA_PROMPT = """你是Spring Boot专家。生成后端基础设施代码(Java 17, Spring Boot 3.2, JPA, MySQL, JWT, Lombok)。

需求: __REQ_DOC__

项目名 huini-barter，包名 com.huini，易货交易平台后端。

严格生成以下文件:
### 1. pom.xml
(依赖: spring-boot-starter-web, spring-boot-starter-data-jpa, spring-boot-starter-security, spring-boot-starter-validation, mysql-connector-j, jjwt-api+impl+jackson 0.12.6, lombok, spring-boot-starter-mail)
### 2. src/main/resources/application.yml
(MySQL: huini_barter, 端口8080, JWT secret+过期时间, 文件上传配置)
### 3. src/main/resources/schema.sql
(建表语句，根据需求文档设计所有核心表)
### 4. src/main/java/com/huini/HuiniApplication.java
### 5. src/main/java/com/huini/common/ApiResponse.java
(统一响应: code, message, data; 静态方法success/fail)
### 6. src/main/java/com/huini/common/GlobalExceptionHandler.java
(@RestControllerAdvice, 处理参数校验异常、业务异常、权限异常)
### 7. src/main/java/com/huini/config/SecurityConfig.java
(放行公开接口, JWT过滤器, CORS配置)
### 8. src/main/java/com/huini/security/JwtTokenProvider.java
(生成token/验证token/获取用户ID)
### 9. src/main/java/com/huini/security/JwtAuthenticationFilter.java
(从Header取token, 验证, 设置SecurityContext)

每个文件用 ### N. 路径 标记，后跟代码块 ```java\n...\n```。只生成这9个文件。确保import完整、代码可编译。
"""

BACKEND_DOMAIN_PROMPT = """你是Spring Boot专家。生成Entity/Enum/Repository/DTO(Java17, Lombok, JPA, 包com.huini)。

API: __API_DOC__

根据易货平台需求设计以下实体:

枚举类:
### 1. src/main/java/com/huini/entity/enums/UserRole.java
(USER普通用户, MERCHANT商家, ADMIN管理员)
### 2. src/main/java/com/huini/entity/enums/AuthStatus.java
(PENDING待审核, APPROVED已认证, REJECTED已驳回)
### 3. src/main/java/com/huini/entity/enums/GoodsStatus.java
(PUBLISHED已发布, TRADING交易中, COMPLETED已完成, CANCELLED已取消)
### 4. src/main/java/com/huini/entity/enums/ConsignmentStatus.java
(PENDING_REVIEW待审核, APPROVED已上架, SELLING售卖中, SOLD已售出, REJECTED已驳回)
### 5. src/main/java/com/huini/entity/enums/OrderStatus.java
(易货订单: PENDING待确认, ACCEPTED已接受, COMPLETED已完成, CANCELLED已取消)
### 6. src/main/java/com/huini/entity/enums/PayStatus.java
(PENDING待支付, PAID已支付, SHIPPED已发货, RECEIVED已收货, COMPLETED已完成, REFUNDED已退款)

实体类:
### 7. src/main/java/com/huini/entity/User.java
(id, phone, password, nickname, avatar, realName, idCard, authStatus, balance余额, role, merchantStatus, createdAt, updatedAt)
### 8. src/main/java/com/huini/entity/Category.java
(id, name品类名, icon图标, sortOrder排序)
### 9. src/main/java/com/huini/entity/Goods.java
(id, userId发布者, categoryId, title, description, images, barterFor易货需求描述, city, district, status, isRecommended, viewCount, createdAt)
### 10. src/main/java/com/huini/entity/ConsignmentItem.java
(id, userId寄卖方, categoryId, title, description, images, price售价, serviceFee服务费(5%), status, createdAt)
### 11. src/main/java/com/huini/entity/BarterOrder.java
(id, goodsId易货商品, fromUserId发起方, toUserId接收方, message留言, status, createdAt)
### 12. src/main/java/com/huini/entity/ConsignmentOrder.java
(id, consignmentItemId寄卖商品, buyerId买家, sellerId卖家, amount金额, serviceFee服务费, status支付状态, payMethod支付方式, addressId收货地址, trackingNo物流单号, createdAt)
### 13. src/main/java/com/huini/entity/Favorite.java
(id, userId, goodsId可为空, consignmentItemId可为空, type类型BARTER/CONSIGNMENT, createdAt)
### 14. src/main/java/com/huini/entity/Address.java
(id, userId, receiverName, phone, province, city, district, detail, isDefault)
### 15. src/main/java/com/huini/entity/Announcement.java
(id, title, content, isActive, createdAt)
### 16. src/main/java/com/huini/entity/Message.java
(id, userId接收者, title, content, isRead, type类型SYSTEM/ORDER/CHAT, refId关联ID, createdAt)
### 17. src/main/java/com/huini/entity/Transaction.java
(id, userId, type收支类型INCOME/EXPENSE, amount金额, balanceAfter, bizType业务类型CONSIGNMENT_SALE/REFUND, bizId关联订单ID, description, createdAt)

Repository (每个实体对应一个):
### 18. src/main/java/com/huini/repository/UserRepository.java
### 19. src/main/java/com/huini/repository/CategoryRepository.java
### 20. src/main/java/com/huini/repository/GoodsRepository.java
### 21. src/main/java/com/huini/repository/ConsignmentItemRepository.java
### 22. src/main/java/com/huini/repository/BarterOrderRepository.java
### 23. src/main/java/com/huini/repository/ConsignmentOrderRepository.java
### 24. src/main/java/com/huini/repository/FavoriteRepository.java
### 25. src/main/java/com/huini/repository/AddressRepository.java
### 26. src/main/java/com/huini/repository/AnnouncementRepository.java
### 27. src/main/java/com/huini/repository/MessageRepository.java
### 28. src/main/java/com/huini/repository/TransactionRepository.java

DTO (请求/响应):
### 29. src/main/java/com/huini/dto/LoginRequest.java
### 30. src/main/java/com/huini/dto/RegisterRequest.java
### 31. src/main/java/com/huini/dto/PublishGoodsRequest.java
### 32. src/main/java/com/huini/dto/ApplyConsignmentRequest.java
### 33. src/main/java/com/huini/dto/CreateBarterOrderRequest.java
### 34. src/main/java/com/huini/dto/CreateConsignmentOrderRequest.java
### 35. src/main/java/com/huini/dto/PageQuery.java
(分页查询: page, size, keyword, categoryId, city, sortBy)
### 36. src/main/java/com/huini/dto/DashboardResponse.java
### 37. src/main/java/com/huini/dto/BalanceResponse.java

每个文件用 ### N. 路径 标记，后跟代码块。只生成上述文件。确保import完整、Lombok注解正确、JPA关系映射合理。
"""

SERVICES_PROMPT = """你是Spring Boot专家。生成Service层(包com.huini.service, @Service, @RequiredArgsConstructor, @Transactional)。

API: __API_DOC__
已有实体: User, Category, Goods, ConsignmentItem, BarterOrder, ConsignmentOrder, Favorite, Address, Announcement, Message, Transaction
已有Repository和DTO

生成以下Service:
### 1. src/main/java/com/huini/service/AuthService.java
(注册/登录/JWT签发、实名认证提交、商家认证申请)
### 2. src/main/java/com/huini/service/UserService.java
(用户信息CRUD、钱包余额查询、交易流水查询、地址管理)
### 3. src/main/java/com/huini/service/GoodsService.java
(发布易货/编辑/下架、列表查询含品类+区域筛选+关键词搜索、详情查询、推荐置顶)
### 4. src/main/java/com/huini/service/BarterOrderService.java
(发起易货意向/接受/拒绝/完成、我的易货列表:我发起的+我收到的、订单状态流转)
### 5. src/main/java/com/huini/service/ConsignmentService.java
(寄卖申请提交含图片、分类、售价、自动计算5%服务费; 审核通过/驳回; 上架/下架)
### 6. src/main/java/com/huini/service/ConsignmentOrderService.java
(寄卖下单/支付(模拟)/发货填物流/确认收货/申请退款; 订单金额+5%服务费自动计算写入Transaction; 卖家结算查询)
### 7. src/main/java/com/huini/service/CategoryService.java
(全品类列表、排序)
### 8. src/main/java/com/huini/service/AnnouncementService.java
(公告CRUD、首页滚动公告)
### 9. src/main/java/com/huini/service/MessageService.java
(消息推送、未读计数、已读标记)
### 10. src/main/java/com/huini/service/FavoriteService.java
(收藏/取消收藏、收藏列表)
### 11. src/main/java/com/huini/service/DashboardService.java
(首页数据:今日推荐、附近货品、同城商家统计)

每个文件用 ### N. 路径 标记，后跟代码块。确保import完整、注入关系正确、事务边界清楚。
"""

CONTROLLERS_PROMPT = """你是Spring Boot专家。生成Controller和数据初始化代码。

API: __API_DOC__
已有Service: Auth, User, Goods, BarterOrder, Consignment, ConsignmentOrder, Category, Announcement, Message, Favorite, Dashboard

Controller (包com.huini.controller, @RestController, @RequestMapping, @RequiredArgsConstructor):
### 1. src/main/java/com/huini/controller/AuthController.java
(POST /api/auth/login 登录, POST /api/auth/register 注册, GET /api/auth/me 当前用户, POST /api/auth/realname 实名认证, POST /api/auth/merchant 商家认证)
### 2. src/main/java/com/huini/controller/GoodsController.java
(POST /api/goods 发布易货, GET /api/goods 列表含筛选, GET /api/goods/{id} 详情, PUT /api/goods/{id} 编辑, DELETE /api/goods/{id} 下架, GET /api/goods/recommended 今日推荐)
### 3. src/main/java/com/huini/controller/BarterOrderController.java
(POST /api/barter-orders 发起易货意向, GET /api/barter-orders 我的易货列表, PUT /api/barter-orders/{id}/accept 接受, PUT /api/barter-orders/{id}/complete 完成, PUT /api/barter-orders/{id}/cancel 取消)
### 4. src/main/java/com/huini/controller/ConsignmentController.java
(POST /api/consignments 申请寄卖, GET /api/consignments 寄卖商品列表, GET /api/consignments/{id} 详情, PUT /api/consignments/{id}/approve 审核通过(管理员), PUT /api/consignments/{id}/reject 驳回(管理员))
### 5. src/main/java/com/huini/controller/ConsignmentOrderController.java
(POST /api/consignment-orders 下单, GET /api/consignment-orders 订单列表, PUT /api/consignment-orders/{id}/pay 支付, PUT /api/consignment-orders/{id}/ship 发货, PUT /api/consignment-orders/{id}/receive 确认收货, PUT /api/consignment-orders/{id}/refund 申请退款)
### 6. src/main/java/com/huini/controller/UserController.java
(PUT /api/user/profile 编辑资料, GET /api/user/balance 余额查询, GET /api/user/transactions 交易流水, POST /api/user/addresses 新增地址, GET /api/user/addresses 地址列表, PUT /api/user/addresses/{id} 编辑, DELETE /api/user/addresses/{id} 删除)
### 7. src/main/java/com/huini/controller/CategoryController.java
(GET /api/categories 全品类列表)
### 8. src/main/java/com/huini/controller/AnnouncementController.java
(GET /api/announcements 公告列表滚动)
### 9. src/main/java/com/huini/controller/MessageController.java
(GET /api/messages 消息列表, GET /api/messages/unread-count 未读数, PUT /api/messages/{id}/read 已读)
### 10. src/main/java/com/huini/controller/FavoriteController.java
(POST /api/favorites 收藏, DELETE /api/favorites/{id} 取消, GET /api/favorites 收藏列表)
### 11. src/main/java/com/huini/controller/DashboardController.java
(GET /api/dashboard 首页数据:推荐货品/寄卖精选/商家列表)
### 12. src/main/java/com/huini/controller/AdminController.java
(GET /api/admin/pending-consignments 待审核寄卖, GET /api/admin/pending-merchants 待审核商家, PUT /api/admin/audit-merchant/{id} 商家审核, GET /api/admin/statistics 后台统计, POST /api/admin/announcements 发公告)

数据初始化 (包com.huini.config, @Configuration):
### 13. src/main/java/com/huini/config/DataInitializer.java
@PostConstruct初始化:
- 7大品类: 五金建材/日用百货/餐饮服务/车辆房产/企业库存/数码家电/本地生活
- 1个管理员账号(admin/123456用BCrypt)
- 3个测试用户(手机13800000001/02/03, 密码123456)
- 5条示例易货商品(不同品类+城市)
- 3条寄卖示例商品
- 2条平台公告

每个文件用 ### N. 路径 标记，后跟代码块。确保权限控制: 用户操作需@PreAuthorize, 管理员操作需ADMIN角色。
"""

VUE_CONFIG_PROMPT = """你是Vue 3 + Vite前端架构师。为汇尼易链(易货交易平台)生成前端配置文件和公共组件。

需求: __REQ_DOC__
后端API: http://localhost:8080/api, JWT Bearer token认证

技术栈: Vue 3 (Composition API + <script setup>), Vue Router 4, Pinia, Vite 5, Axios
设计风格: 移动端优先(mobile-first), 白色底+蓝色主色调(#1677ff)+红色强调(#ff4d4f用于发布按钮), 大字体大图标, 卡片式布局

每个文件用 ## N. frontend/路径 标记，后跟代码块 ```lang\n完整代码\n```。

生成以下文件:
## 1. frontend/package.json
## 2. frontend/vite.config.js
## 3. frontend/index.html
## 4. frontend/src/main.js
## 5. frontend/src/App.vue (含底部5栏导航固定: 首页/易货广场/发布/寄卖商城/我的, 登录页不显示)
## 6. frontend/src/style.css (移动端优先max-width:750px, 主色#1677ff, 大按钮48px, 卡片圆角12px, 底部导航56px)
## 7. frontend/src/api/index.js (Axios实例+拦截器+所有API函数)
## 8. frontend/src/router/index.js (所有路由+守卫)
## 9. frontend/src/stores/auth.js (Pinia: user/token/登录/退出)
## 10. frontend/src/components/BottomNav.vue (底部5栏固定导航, 发布按钮红色凸起)
## 11. frontend/src/components/GoodsCard.vue (易货卡片: 图片+标题+需求+城市)
## 12. frontend/src/components/ConsignmentCard.vue (寄卖卡片: 图片+标题+价格+5%标签)

只生成这12个文件。确保import完整、路由正确、API函数齐全。
"""

VUE_VIEWS_PROMPT = """你是Vue 3 + Vite前端架构师。为汇尼易链生成所有视图页面。

后端API: http://localhost:8080/api
设计风格: 移动端优先, #1677ff主色, 大字体大触控区域, 卡片布局
已有组件: BottomNav, GoodsCard, ConsignmentCard; 路由和API已配置

每个文件用 ## N. frontend/路径 标记，后跟代码块 ```lang\n完整代码\n```。

生成以下页面:
## 1. frontend/src/views/Login.vue
(居中卡片, LOGO+名称, 手机号密码表单, 登录/注册tab, 成功后跳首页)
## 2. frontend/src/views/Home.vue
(完整首页: 顶栏LOGO+品牌名+消息客服图标, 滚动公告, 搜索栏, 8宫格金刚区2行4列发布易货红色高亮, 核心标语"点对点免费易货·全程零交易佣金", 今日推荐横向滑动GoodsCard, 寄卖专区浅橙背景横向ConsignmentCard, 7品类标签, 同城商家, 底部承诺通栏, 全部API获取)
## 3. frontend/src/views/BarterSquare.vue
(易货广场: 筛选栏品类/区域/排序, 列表GoodsCard, 上拉加载分页)
## 4. frontend/src/views/GoodsDetail.vue
(轮播图, 标题, 发布人信息, 易货需求, 位置, 底栏收藏+发起易货按钮)
## 5. frontend/src/views/Publish.vue
(顶部tab: 发布易货|申请寄卖; 易货表单含图片上传分类城市; 寄卖表单含售价+自动计算5%服务费)
## 6. frontend/src/views/ConsignmentShop.vue
(寄卖商城: 品类筛选, 网格ConsignmentCard, 购物车浮动按钮)
## 7. frontend/src/views/ConsignmentDetail.vue
(轮播图, 价格大字红色, 5%服务费说明, 底栏购物车+立即购买)
## 8. frontend/src/views/Checkout.vue
(收货地址, 商品清单, 金额明细含5%服务费, 支付方式, 提交订单)
## 9. frontend/src/views/Mine.vue
(头像昵称认证状态, 钱包卡片余额, 菜单:我的易货/我的寄卖/收藏/地址/消息/商家管理/规则/关于/客服/退出, 无代理入口)
## 10. frontend/src/views/MyBarterOrders.vue
(tab:我发起的/我收到的, 订单卡片状态标签操作按钮)
## 11. frontend/src/views/MyConsignmentOrders.vue
(tab:全部/待付款/待发货/待收货/已完成, 订单卡片物流)
## 12. frontend/src/views/Wallet.vue
(余额大字, 交易流水列表仅寄卖收支, 收支筛选)
## 13. frontend/src/views/MyFavorites.vue
(tab易货/寄卖, 收藏列表, 取消收藏)
## 14. frontend/src/views/MyAddresses.vue
(地址列表, 默认标记, 新增编辑弹窗含省市区)
## 15. frontend/src/views/MyMessages.vue
(消息列表分类, 未读红点, 左滑删除)
## 16. frontend/src/views/MerchantManage.vue
(已认证商家: 货品管理上下架, 店铺信息编辑, 寄卖管理, 简单统计)

只生成这16个文件，确保代码完整可运行，import路径正确。
"""
```

- [ ] **Step 2: Verify syntax**

```bash
uv run python -c "from prompts import DOCS_PROMPT, BACKEND_INFRA_PROMPT, fill; print(f'fill test: {fill(\"hello __NAME__\", NAME=\"world\")}')"
```

Expected: `fill test: hello world`

- [ ] **Step 3: Commit**

```bash
git add F:\Agent\Test\prompts.py
git commit -m "refactor: extract prompt templates to prompts.py"
```

---

### Task 3: Create `generators.py`

**Files:**
- Create: `F:\Agent\Test\generators.py`

- [ ] **Step 1: Write generators.py**

```python
"""LLM generation step functions for SeedStack workflow."""

import os

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
```

- [ ] **Step 2: Verify syntax**

```bash
uv run python -c "from generators import generate_docs, gen_backend_infra, gen_backend_domain, gen_services, gen_controllers, gen_vue_config_components, gen_vue_views; print('All 7 generator functions loaded')"
```

Expected: `All 7 generator functions loaded`

- [ ] **Step 3: Commit**

```bash
git add F:\Agent\Test\generators.py
git commit -m "refactor: extract generator functions to generators.py"
```

---

### Task 4: Create `builder.py`

**Files:**
- Create: `F:\Agent\Test\builder.py`

- [ ] **Step 1: Write builder.py**

```python
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
```

- [ ] **Step 2: Verify syntax**

```bash
uv run python -c "from builder import create_project, auto_build_fix, _collect_source_files, _fix_and_rewrite; print('All builder functions loaded')"
```

Expected: `All builder functions loaded`

- [ ] **Step 3: Commit**

```bash
git add F:\Agent\Test\builder.py
git commit -m "refactor: extract project builder and build/repair to builder.py"
```

---

### Task 5: Create `workflow.py`

**Files:**
- Create: `F:\Agent\Test\workflow.py`

- [ ] **Step 1: Write workflow.py**

```python
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
        # Wrap step to inject model into LLM-based functions
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
```

- [ ] **Step 2: Verify syntax**

```bash
uv run python -c "from workflow import build_agent; print('build_agent loaded')"
```

Expected: `build_agent loaded`

- [ ] **Step 3: Commit**

```bash
git add F:\Agent\Test\workflow.py
git commit -m "refactor: extract workflow assembly to workflow.py"
```

---

### Task 6: Refactor `main.py`

**Files:**
- Modify: `F:\Agent\Test\main.py` — replace entire content

- [ ] **Step 1: Replace main.py with slimmed entry point**

```python
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
```

- [ ] **Step 2: Verify syntax**

```bash
uv run python -c "import main; print('main.py loaded, agent=%s' % type(main.agent).__name__)"
```

Expected: `main.py loaded, agent=CompiledStateGraph`

- [ ] **Step 3: Commit**

```bash
git add F:\Agent\Test\main.py
git commit -m "refactor: slim main.py to entry point only (817 → 46 lines)"
```

---

### Task 7: Remove unused dependency

**Files:**
- Modify: `F:\Agent\Test\pyproject.toml`

- [ ] **Step 1: Remove langchain-anthropic from dependencies**

Edit `pyproject.toml`, remove the line:
```
"langchain-anthropic>=1.4.3",
```

- [ ] **Step 2: Re-sync dependencies**

```bash
uv sync
```

Expected: uv removes langchain-anthropic and its transitive deps

- [ ] **Step 3: Commit**

```bash
git add F:\Agent\Test\pyproject.toml F:\Agent\Test\uv.lock
git commit -m "chore: remove unused langchain-anthropic dependency"
```

---

### Task 8: End-to-end smoke test

- [ ] **Step 1: Verify all modules import cleanly**

```bash
uv run python -c "
from extractors import FileEntry, extract_files, dump_debug, STRATEGIES
from prompts import fill, DOCS_PROMPT, BACKEND_INFRA_PROMPT, BACKEND_DOMAIN_PROMPT
from prompts import SERVICES_PROMPT, CONTROLLERS_PROMPT, VUE_CONFIG_PROMPT, VUE_VIEWS_PROMPT
from generators import generate_docs, gen_backend_infra, gen_backend_domain
from generators import gen_services, gen_controllers, gen_vue_config_components, gen_vue_views
from builder import create_project, auto_build_fix
from workflow import build_agent
import main
print('All imports OK')
print(f'extractors: {len(STRATEGIES)} strategies')
print(f'agent type: {type(main.agent).__name__}')
print('SMOKE TEST PASSED')
"
```

Expected output ends with `SMOKE TEST PASSED`

- [ ] **Step 2: Verify file sizes (refactored main.py should be small)**

```bash
wc -l F:\Agent\Test\main.py F:\Agent\Test\extractors.py F:\Agent\Test\prompts.py F:\Agent\Test\generators.py F:\Agent\Test\builder.py F:\Agent\Test\workflow.py
```

Expected: main.py under 50 lines, each module under 350 lines

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "test: add end-to-end smoke test verification"
```
