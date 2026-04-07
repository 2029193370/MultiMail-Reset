# ci-templates

企业通用 CI 工作流模板，自动检测项目语言并执行对应的质量检查与安全扫描。

## 支持的技术栈

| 技术栈 | 检测文件 | 执行内容 |
|--------|----------|----------|
| Node.js / TypeScript / Next.js / React | `package.json` | `npm ci` → `npm run lint` → `npm run build` |
| Java (Maven) | `pom.xml` | `mvn -B compile`（自动识别 Maven Wrapper） |
| Java (Gradle) | `build.gradle` / `build.gradle.kts` | `gradle assemble`（自动识别 Gradle Wrapper） |
| PHP / Laravel | `composer.json` / `*.php` | `composer install` → `php -l` 语法检查 |
| Python / Django / FastAPI | `requirements.txt` / `Pipfile` / `pyproject.toml` | Flake8 致命错误检查 |
| Go | `go.mod` | `go vet` → `go build` |
| .NET / C# | `*.csproj` / `*.sln` | `dotnet restore` → `dotnet build` |
| Docker | `Dockerfile` | Hadolint 最佳实践与安全检查 |

## 流水线结构

| Layer | 内容 | 说明 |
|-------|------|------|
| Layer 0 | 仓库卫生检查 | 编译产物、合并冲突标记、敏感文件（`.env`/私钥）、大文件检测 |
| Layer 1 | Lint & Build 检查 | 根据项目文件自动检测语言，执行对应的语法检查和编译 |
| Layer 2 | Trivy 安全漏洞 & 密钥泄露扫描 | 同时扫描依赖漏洞和硬编码密钥 |

> **执行策略**：所有 Layer 的所有检查项全量执行，不会因某项失败而跳过后续检查。开发者可在一次 CI 运行中看到全部问题，一次性修复。

---

## 新项目接入（2 步）

### 第 1 步：复制 starter 文件

将 [`starter/.github/workflows/ci.yml`](./starter/.github/workflows/ci.yml) 复制到你的新项目，保持相同路径：

```
你的新项目/
└── .github/
    └── workflows/
        └── ci.yml   ← 复制这个文件
```

### 第 2 步：按需修改版本（可选）

打开 `ci.yml`，取消注释并修改你需要的语言版本：

```yaml
jobs:
  ci:
    uses: 2029193370/ci-templates/.github/workflows/reusable-ci.yml@main
    with:
      node-version: '22'       # Node.js / TypeScript / Next.js
      java-version: '17'       # Java (Maven / Gradle)
      php-version: '8.2'       # PHP / Laravel
      python-version: '3.11'   # Python / Django
      go-version: '1.22'       # Go
      dotnet-version: '8.0'    # .NET / C#
```

**不需要传入的参数保持注释或删掉即可**，工作流会自动根据项目中存在的文件判断执行哪些检查。

---

## 升级维护

只需修改本仓库的 `reusable-ci.yml`，所有接入项目**自动获得更新**，无需逐个修改。

---

## 安全与性能特性

- **全量执行不中断** — 所有检查项全部跑完再汇总报告，开发者一次看到所有问题，避免反复修复-推送
- **最小权限原则** — 工作流仅声明 `contents: read`，限制 Token 作用范围
- **并发控制** — 同一分支重复推送自动取消旧流水线，节省 Actions 分钟数
- **仓库卫生检查** — 拦截编译产物、合并冲突标记、大文件（>5MB），警告 `.env`/私钥等敏感文件
- **Dockerfile 规范** — 自动检测 Dockerfile 并用 Hadolint 检查安全与最佳实践
- **超时保护** — 所有 Job 设置超时（Layer 0: 5min，Layer 1: 20min，Layer 2: 15min），防止挂起
- **依赖缓存** — npm / Maven / Gradle / Composer / pip / Go modules 均启用缓存
- **显式扫描器** — Trivy 同时启用 `vuln`（漏洞）+ `secret`（密钥泄露）扫描

---

## 添加状态徽章

在项目 README 顶部添加：

```markdown
![CI](https://github.com/<你的用户名>/<你的仓库>/actions/workflows/ci.yml/badge.svg)
```
