-- 在 MySQL 中执行（命令行或 Navicat / Workbench）
-- mysql -u root -p < scripts/create_mysql_db.sql

CREATE DATABASE IF NOT EXISTS family_finance
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 如需单独建用户（可选，把密码改成你的）：
-- CREATE USER IF NOT EXISTS 'ff_user'@'localhost' IDENTIFIED BY 'ff_pass123';
-- GRANT ALL PRIVILEGES ON family_finance.* TO 'ff_user'@'localhost';
-- FLUSH PRIVILEGES;
