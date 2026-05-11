# 学生管理系统

基于 Python 与 Flask 的轻量级教务辅助应用，适合本地部署、课程演示或小型班级管理。提供学生档案、班级、课程、选课、成绩与考勤等模块，并配有统一的深色界面。

## 功能概览

| 模块 | 说明 |
|------|------|
| **工作台** | 学生、班级、课程、成绩数量及当日考勤条数汇总 |
| **学生** | 名册检索（姓名 / 学号 / 班级）、增删改；支持分班 |
| **班级** | 班级档案（年级、班码、班主任等）；有学生挂靠时不可删除 |
| **课程** | 课程信息维护；删除课程将级联清除选课、成绩与考勤 |
| **选课** | 在课程下为学生添加或退选；退选会清除该生在该课下的成绩与考勤 |
| **成绩** | 按课程、班级、关键词筛选；须先选课；同一学生 + 课程 + 成绩项名称唯一 |
| **考勤** | 列表筛选；单条登记或编辑；支持按课程 + 日期批量登记全班 |

## 技术栈

- **Python** 3.10+（建议 3.11+）
- **Flask** 3、**Jinja2** 模板
- **Flask-SQLAlchemy**、**SQLite**（默认单文件数据库）
- **Flask-Login** 会话登录
- **Bootstrap** 5.3、**Bootstrap Icons**（CDN）
- **python-dotenv** 读取环境变量

## 目录结构

```
student_mgmt/
├── app/
│   ├── __init__.py      # 应用工厂、扩展初始化、建表与默认管理员
│   ├── models.py        # ORM：用户、班级、学生、课程、选课、成绩、考勤
│   ├── routes.py        # 全部路由与业务逻辑
│   ├── extensions.py    # db、login_manager
│   ├── db_migrate.py    # SQLite 轻量迁移（兼容旧 students 表）
│   ├── static/
│   │   └── style.css    # 全局样式
│   └── templates/       # Jinja2 页面
├── instance/            # 默认存放 students.db（可加入 .gitignore）
├── config.py            # 配置类
├── run.py               # 开发环境启动入口
├── requirements.txt
├── .env.example         # 环境变量示例
└── README.md
```

## 快速开始

### 1. 创建虚拟环境并安装依赖

```bash
cd student_mgmt
python -m venv .venv
```

**Windows（PowerShell）**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux**

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 启动应用

```bash
python run.py
```

默认监听 **http://127.0.0.1:5000** ，浏览器访问即可。

### 3. 默认管理员

首次启动会自动创建管理员账号（若库中尚不存在同名用户）：

| 项 | 默认值 |
|----|--------|
| 用户名 | `admin` |
| 密码 | `admin123` |

**务必在生产或公网环境中修改密码**，并通过环境变量设置强随机 `SECRET_KEY`。

## 环境变量

可复制 `.env.example` 为 `.env` 并按需修改：

| 变量 | 说明 |
|------|------|
| `SECRET_KEY` | Flask 会话密钥，生产环境必填 |
| `DATABASE_URL` | 数据库连接串；不设置则使用 `instance/students.db` |
| `DEFAULT_ADMIN_USERNAME` | 首次创建的默认管理员用户名 |
| `DEFAULT_ADMIN_PASSWORD` | 首次创建的默认管理员密码 |

## 推荐使用流程

1. 创建 **班级**，再维护 **学生** 并选择所属班级。  
2. 创建 **课程**，在课程页的 **选课** 中为需要上课的学生勾选课程。  
3. 在 **成绩** 中录入各成绩项（须已选课）。  
4. 在 **考勤** 中使用单条或 **批量考勤** 按课程、日期登记出勤情况。

## 数据库与迁移

- 默认使用项目根目录下 `instance/students.db`（启动时会自动创建 `instance` 目录）。  
- `app/db_migrate.py` 在 SQLite 下会为旧版 `students` 表补充 `class_id` 字段，并在支持的前提下尝试删除已废弃的 `class_name` 列。  
- 若本地数据库结构异常或希望完全重建，请先**停止运行中的应用**，再删除 `instance/students.db` 后重新启动（会重新建表并再次写入默认管理员，前提是用户名仍不存在）。

## 安全提示

- 默认账号与 `SECRET_KEY` 仅适用于本地开发。  
- 不要将包含真实密码的 `.env` 提交到版本库（仓库中已忽略 `.env`）。  
- 本系统未内置 CSRF Token；若部署到公网，请自行加固（如 HTTPS、反向代理、CSRF 防护等）。

## 开发说明

- `run.py` 中 `debug=True` 仅适合开发调试；生产部署请使用 **Gunicorn / Waitress** 等 WSGI 服务器，并关闭调试模式。  
- 前端依赖通过 CDN 引入，离线环境需自行改为本地静态资源。

## 许可证

本项目可按需自由使用与修改；用于商业或分发时请自行评估合规性与责任。
