# MailGuard - 个人邮箱自动改密码系统

周期性自动修改个人邮箱密码，确保账号安全。

## 功能

- **多邮箱管理**：支持 QQ邮箱、网易邮箱(163/126)、Outlook/Hotmail、Gmail
- **自动改密**：通过浏览器自动化 (Playwright) 尝试自动修改密码
- **混合模式**：自动化失败时（验证码/2FA），降级为手动模式并提供指引
- **定时调度**：按设定周期（如每30天）自动触发改密
- **密码生成**：内置强密码生成器，支持自定义规则
- **加密存储**：所有密码使用 Fernet 对称加密存储
- **变更历史**：完整记录每次密码变更的详情

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Ant Design 5 |
| 后端 | FastAPI + SQLAlchemy 2 (async) |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |
| 自动化 | Playwright (Chromium) |
| 调度 | APScheduler |

## 本地开发

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173，API 文档 http://localhost:8000/docs

### Docker Compose

```bash
docker compose up -d
```

访问 http://localhost

## 安全提示

- 修改 `.env` 中的 `ENCRYPTION_KEY` 为强随机字符串
- 本工具仅供个人本地使用，不要部署在公网
- 密码以加密形式存储在数据库中
