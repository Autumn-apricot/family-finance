# 家庭资产管理 — 后端 API

基于 `docs/` 设计文档的 Django 4.2 + DRF 实现，**默认使用 MySQL 8.0**。

## 一、MySQL 准备

### 1. 安装并启动 MySQL

确保本机 MySQL 8.0 已运行（服务名常为 `MySQL80`）。

### 2. 创建数据库

```bat
mysql -u root -p < scripts\create_mysql_db.sql
```

或在客户端执行：

```sql
CREATE DATABASE IF NOT EXISTS family_finance
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 配置连接

```bat
copy .env.example .env
```

编辑 `.env`，**至少修改** `DB_PASSWORD` 为你的 root 密码：

```ini
DB_ENGINE=mysql
DB_NAME=family_finance
DB_USER=root
DB_PASSWORD=你的密码
DB_HOST=127.0.0.1
DB_PORT=3306
```

## 二、启动后端

```bat
cd code\family_finance
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations finance
python manage.py migrate
python scripts\init_data.py
python manage.py runserver 0.0.0.0:8000
```

- 健康检查：http://127.0.0.1:8000/api/health/
- 管理员：`admin` / `admin123`
- 测试成员：`zhangsan` / `123456`

## 三、常见问题

| 问题 | 处理 |
|------|------|
| `Access denied for user` | 检查 `.env` 中 `DB_USER` / `DB_PASSWORD` |
| `Unknown database 'family_finance'` | 先执行 `scripts/create_mysql_db.sql` |
| `Can't connect to MySQL server` | 确认 MySQL 服务已启动、端口 3306 |
| `No module named 'pymysql'` | `pip install PyMySQL` |
| 想用 mysqlclient | `pip install mysqlclient`，`.env` 设 `DB_USE_PYMYSQL=false` |

## 四、改用 SQLite（可选）

`.env` 中设置：

```ini
DB_ENGINE=sqlite
```

然后重新 `python manage.py migrate`。

## 五、小程序 / Web 联调

见上级目录 [`../README.md`](../README.md)。
