# 校园配送服务管理系统

这是一个基于 Django REST Framework + Vue 3 的校园配送服务管理系统 MVP，已将物流配送场景重新设计为校园快递代取、外卖配送和物品帮送场景。

## 已实现功能

- 学生、配送员、管理员三类角色登录注册
- 学生发布配送订单、查看订单、取消未完成订单
- 配送员查看待接订单、接单、取件、配送、确认送达
- 管理员查看全部订单和运营数据
- 订单状态严格按“待接单 → 已接单 → 取件中 → 配送中 → 已完成”流转
- 订单统计、完成金额、配送员/学生数量统计
- SQLite 本地数据库和演示数据

## 目录

```text
manage.py                 Django 启动入口
server/                   Django 项目配置
delivery/                 用户、订单、评价业务
web/                      Vue 3 前端
db.sqlite3                本地数据库（首次迁移后生成）
```

## 启动后端

在项目根目录执行：

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:18000
```

## 启动前端

新开一个终端：

```powershell
cd web
npm install
npm run dev
```

浏览器访问 `http://127.0.0.1:5173`。

## 演示账号

| 账号 | 密码 | 身份 |
|---|---|---|
| student | 123456 | 学生 |
| courier | 123456 | 配送员 |
| admin | 123456 | 管理员 |

## API 入口

- `POST /api/auth/register/` 注册
- `POST /api/auth/login/` 登录并返回 Token
- `GET /api/orders/` 当前角色可见订单
- `POST /api/orders/` 学生发布订单
- `POST /api/orders/{id}/accept/` 配送员接单
- `POST /api/orders/{id}/change_status/` 更新配送状态
- `GET /api/orders/stats/` 订单统计

生产环境使用时，请将 `server/settings.py` 中的密钥、DEBUG、ALLOWED_HOSTS 和数据库配置改为正式值，并配置 HTTPS。
