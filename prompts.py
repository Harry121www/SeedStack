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
