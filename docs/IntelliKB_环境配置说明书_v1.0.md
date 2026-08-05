# IntelliKB 环境配置说明书

<table>
  <thead>
    <tr><th>项目</th><th>内容</th></tr>
  </thead>
  <tbody>
    <tr><td>文档版本</td><td>V1.0</td></tr>
    <tr><td>适用范围</td><td>IntelliKB 本地开发、测试环境、云服务器生产环境</td></tr>
    <tr><td>基线依据</td><td><code>IntelliKB_需求说明文档_v1.2.md</code></td></tr>
    <tr><td>部署方式</td><td>Docker Compose（开发/测试）与 Kubernetes（生产可选）</td></tr>
  </tbody>
</table>

---

## 1. 目的与边界

本文定义 IntelliKB 的运行环境、配置项和部署检查方式。系统采用容器化部署：前端、后端、异步任务、数据库、缓存、对象存储、反向代理及监控组件均可独立运行于 Docker 容器中。

本说明书是目标部署基线。当前仓库尚未包含应用代码、`Dockerfile`、`compose.yaml` 或 Kubernetes 清单；文中出现的镜像名称、端口和环境变量是后续实现应遵循的约定，部署前应以实际代码中的配置为准。

## 2. 部署架构

```text
浏览器
  |
HTTPS :443
  v
Nginx / Ingress
  |--------------------> React 前端
  |
  +--------------------> FastAPI 后端
                             |-- PostgreSQL + PGVector
                             |-- MongoDB
                             |-- Redis
                             |-- MinIO / 阿里云 OSS
                             |-- Celery Worker
                             +-- OpenAI / 通义千问 / DeepSeek API

Prometheus <---- 应用指标 ----> Grafana
```

除 Nginx 的 80/443 端口外，PostgreSQL、MongoDB、Redis、MinIO 管理端口和监控端口均应限制在 Docker 内部网络或服务器内网，不直接暴露至公网。

## 3. 服务与技术栈

<table>
  <thead>
    <tr><th>服务</th><th>目标技术</th><th>职责</th><th>是否容器化</th></tr>
  </thead>
  <tbody>
    <tr><td>Web 前端</td><td>React + TypeScript + Tailwind CSS</td><td>管理后台、文件上传、聊天与看板</td><td>是</td></tr>
    <tr><td>API 服务</td><td>Python 3.11 + FastAPI</td><td>REST API、JWT 鉴权、RAG 编排、SSE/WebSocket</td><td>是</td></tr>
    <tr><td>异步任务</td><td>Celery Worker</td><td>文档解析、切片、向量化</td><td>是</td></tr>
    <tr><td>消息队列/缓存</td><td>Redis</td><td>Celery Broker、缓存、任务状态</td><td>是</td></tr>
    <tr><td>关系与向量数据</td><td>PostgreSQL + PGVector</td><td>租户、用户、权限、业务数据和向量检索</td><td>是</td></tr>
    <tr><td>对话记录</td><td>MongoDB</td><td>对话与消息历史</td><td>是</td></tr>
    <tr><td>文件存储</td><td>MinIO（开发）/阿里云 OSS（生产）</td><td>原始文档对象存储</td><td>是（MinIO）</td></tr>
    <tr><td>反向代理</td><td>Nginx</td><td>HTTPS、静态资源、反向代理、子域名路由</td><td>是</td></tr>
    <tr><td>可观测性</td><td>Prometheus + Grafana</td><td>指标采集、仪表盘和告警</td><td>是</td></tr>
  </tbody>
</table>

## 4. 环境规格

### 4.1 本地开发环境

<table>
  <thead>
    <tr><th>项目</th><th>最低建议</th><th>推荐</th></tr>
  </thead>
  <tbody>
    <tr><td>操作系统</td><td>Windows 10/11、macOS 或 Linux</td><td>Windows 11 + WSL 2 / Linux</td></tr>
    <tr><td>Docker</td><td>Docker Desktop 4.x 或 Docker Engine 24+</td><td>Docker Engine / Desktop 最新稳定版</td></tr>
    <tr><td>Docker Compose</td><td>Compose V2</td><td>Compose V2 最新稳定版</td></tr>
    <tr><td>CPU</td><td>4 核</td><td>8 核</td></tr>
    <tr><td>内存</td><td>8 GB</td><td>16 GB</td></tr>
    <tr><td>可用磁盘</td><td>30 GB SSD</td><td>60 GB SSD</td></tr>
  </tbody>
</table>

Windows 开发机应启用 WSL 2 后端，并将项目目录放在可被 Docker Desktop 访问的位置。不要在容器中使用 Windows 宿主机路径作为业务配置值。

### 4.2 云服务器生产环境

单机生产起步建议使用 Ubuntu Server 22.04 LTS 或 24.04 LTS：8 核 CPU、16 GB 内存、100 GB SSD。文档量、并发数或向量规模增大后，应优先将 PostgreSQL、MongoDB、Redis、MinIO/OSS 拆分为受管服务或独立节点。

服务器需开放：

<table>
  <thead>
    <tr><th>端口</th><th>用途</th><th>公网开放</th></tr>
  </thead>
  <tbody>
    <tr><td>22</td><td>SSH 运维</td><td>仅固定运维 IP</td></tr>
    <tr><td>80</td><td>HTTP 跳转 HTTPS/证书校验</td><td>是</td></tr>
    <tr><td>443</td><td>HTTPS 访问</td><td>是</td></tr>
    <tr><td>其余端口</td><td>数据库、缓存、对象存储、监控</td><td>否</td></tr>
  </tbody>
</table>

## 5. 配置文件与密钥管理

### 5.1 文件约定

建议在项目根目录保留以下文件：

```text
compose.yaml                 # 服务编排，不写入任何真实密钥
.env.example                 # 可提交，提供所有变量名和示例值
.env                         # 不提交，保存本地或服务器真实配置
deploy/nginx/                # Nginx 配置
deploy/prometheus/           # Prometheus 配置
deploy/k8s/                  # 生产环境 Kubernetes 清单（启用 K8s 时）
```

`.env`、私钥、TLS 证书、数据库备份和 API Key 必须写入 `.gitignore`。GitHub 仓库使用私有仓库；自动部署所需的密钥写入 GitHub Secrets，不提交到代码中。

### 5.2 `.env.example` 基线

```dotenv
# 对外访问
APP_ENV=production
APP_DOMAIN=intellikb.example.com
HTTPS_ENABLED=true

# 认证与加密：生产环境必须替换为随机强密钥
JWT_SECRET=replace-with-a-random-secret
API_KEY_ENCRYPTION_KEY=replace-with-a-32-byte-aes-key

# PostgreSQL + PGVector
POSTGRES_DB=intellikb
POSTGRES_USER=intellikb_app
POSTGRES_PASSWORD=replace-with-a-strong-password
DATABASE_URL=postgresql+asyncpg://intellikb_app:replace-with-a-strong-password@postgres:5432/intellikb

# MongoDB
MONGO_INITDB_ROOT_USERNAME=intellikb_mongo
MONGO_INITDB_ROOT_PASSWORD=replace-with-a-strong-password
MONGODB_URL=mongodb://intellikb_mongo:replace-with-a-strong-password@mongodb:27017/intellikb?authSource=admin

# Redis/Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# MinIO（开发或自建生产对象存储）
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=replace-with-minio-access-key
MINIO_SECRET_KEY=replace-with-minio-secret-key
MINIO_BUCKET=intellikb-documents
MINIO_USE_SSL=false

# 大模型：采用平台默认模型时配置；BYOK 由租户在应用内加密保存
LLM_PROVIDER=deepseek
LLM_API_KEY=replace-with-platform-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

`API_KEY_ENCRYPTION_KEY` 用于加密租户的 BYOK 密钥；应用前端只能展示掩码，不得返回明文。任何示例值均不可直接用于生产环境。

## 6. Docker Compose 部署要求

### 6.1 组件要求

后续 `compose.yaml` 至少应编排以下服务：`nginx`、`frontend`、`api`、`worker`、`postgres`、`mongodb`、`redis`、`minio`、`prometheus`、`grafana`。

关键约束：

- `api` 与 `worker` 必须使用同一份应用镜像及 `.env` 配置，但运行不同启动命令。
- PostgreSQL 必须安装 PGVector 扩展，并在初始化迁移中执行 `CREATE EXTENSION IF NOT EXISTS vector;`。
- 所有有状态组件必须使用命名 Volume 或外部持久化磁盘；容器重建不得丢失数据。
- `api` 提供健康检查端点，例如 `/healthz`；Nginx 仅向健康实例转发请求。
- SSE 响应必须禁用代理缓冲；WebSocket 需正确传递 `Upgrade` 和 `Connection` 请求头。
- 数据库、Redis、MinIO 和 Grafana 不映射宿主机公网端口。

### 6.2 启动步骤

在项目根目录完成实际配置后，执行：

```powershell
Copy-Item .env.example .env
# 编辑 .env，替换全部 replace-with-* 值
docker compose pull
docker compose up -d --build
docker compose ps
```

首次启动后执行数据库迁移和对象存储 Bucket 初始化。具体命令由后续后端项目的迁移工具和初始化脚本确定，推荐使用 Alembic 管理 PostgreSQL Schema。

停止服务使用：

```powershell
docker compose down
```

不要使用带 `-v` 的停止命令，除非已完成备份并确认需要清空全部持久化数据。

## 7. Nginx 与域名配置

生产环境建议采用以下域名约定：

<table>
  <thead>
    <tr><th>域名</th><th>用途</th></tr>
  </thead>
  <tbody>
    <tr><td><code>intellikb.example.com</code></td><td>平台主入口和超级管理员入口</td></tr>
    <tr><td><code>{tenant}.intellikb.example.com</code></td><td>租户子域名入口</td></tr>
    <tr><td><code>api.intellikb.example.com</code></td><td>可选的独立 API 域名</td></tr>
  </tbody>
</table>

DNS 需为主域名和通配符子域名配置解析。若使用 HTTPS，证书必须覆盖主域名及 `*.intellikb.example.com`。Nginx/Ingress 应把原始 Host 请求头传递给 FastAPI，使后端可结合 JWT 中的 `tenant_id` 进行租户校验；域名不能作为唯一鉴权依据。

## 8. 云服务器部署流程

1. 准备 Linux 服务器、域名解析、Docker Engine 和 Docker Compose V2。
2. 在服务器上创建受限部署用户，配置 SSH 密钥登录并关闭密码登录。
3. 通过 GitHub 私有仓库拉取受保护分支的发布版本；服务器不保存开发者个人 API Key。
4. 根据 `.env.example` 创建生产 `.env`，从受控密钥系统或 GitHub Secrets 注入真实密钥。
5. 配置 Nginx、TLS 证书、防火墙和数据盘挂载，再启动 Docker Compose。
6. 执行数据库迁移、初始化管理员账号、创建 MinIO Bucket，并验证服务健康状态。
7. 配置 PostgreSQL/MongoDB/MinIO 的定时备份和 Prometheus 告警。

生产升级采用“拉取已验证镜像或版本标签 -> 数据库迁移 -> 滚动重建 API/Worker -> 健康检查 -> 观察监控”的流程。升级前必须先备份数据库和对象存储。

## 9. Kubernetes 生产扩展

当单机 Docker Compose 无法满足高可用、弹性扩容或滚动发布需求时，迁移至 Kubernetes：

<table>
  <thead>
    <tr><th>Docker Compose 服务</th><th>Kubernetes 对应资源</th></tr>
  </thead>
  <tbody>
    <tr><td>frontend/api/worker</td><td>Deployment</td></tr>
    <tr><td>API 对外访问</td><td>Service + Ingress</td></tr>
    <tr><td>配置/密钥</td><td>ConfigMap + Secret</td></tr>
    <tr><td>PostgreSQL/MongoDB/Redis/MinIO</td><td>优先使用云受管服务；自建时使用 StatefulSet + PVC</td></tr>
    <tr><td>指标监控</td><td>Prometheus Operator + Grafana</td></tr>
  </tbody>
</table>

生产 Kubernetes 不建议将数据库作为无备份的普通容器运行。应为每个环境隔离命名空间、密钥和存储卷，并使用 Ingress 支持租户子域名路由。

## 10. 安全与数据隔离检查

- 强制 HTTPS；HTTP 仅用于跳转 HTTPS 或证书校验。
- JWT 必须包含 `user_id`、`tenant_id` 和 `role`，服务端每次请求校验权限与租户归属。
- PostgreSQL 表、PGVector 检索条件、MongoDB 文档、Redis Key、Celery 任务和对象存储路径必须携带 `tenant_id`。
- 原始文件对象路径使用 `/tenant-{tenant_id}/` 前缀；对象存储 Bucket 不公开读写。
- 租户自定义模型 API Key 使用 AES-256 加密保存，日志中不得记录完整密钥、授权头或文档正文。
- 设置上传文件大小、类型白名单、病毒扫描策略和解析超时，避免恶意文件影响 Worker。
- 定期更新基础镜像和依赖，扫描容器镜像漏洞。

## 11. 上线验收清单

- [ ] `docker compose ps` 中所有必需服务为运行状态且健康检查通过。
- [ ] 主域名、租户子域名和 HTTPS 证书均可访问。
- [ ] 登录、JWT 鉴权、角色权限与跨租户访问拒绝均已验证。
- [ ] 文档上传后可查看 WebSocket 进度，Worker 能完成解析、切片和向量化。
- [ ] SSE 问答可以连续流式返回，并仅检索当前 `tenant_id` 的向量数据。
- [ ] PostgreSQL、MongoDB、Redis、MinIO 不暴露公网端口。
- [ ] 日志带有 `tenant_id`，Prometheus 与 Grafana 可查看 API、Worker、数据库等关键指标。
- [ ] 已完成并演练 PostgreSQL、MongoDB 与对象存储的恢复流程。
- [ ] `.env`、证书、备份与真实 API Key 未提交至 GitHub。

## 12. 待开发阶段确认项

以下配置需在代码实现或架构设计阶段最终确认：数据库迁移命令、镜像仓库地址、健康检查路径、模型供应商适配参数、文件扫描方案、备份保留周期、Kubernetes 集群与云服务选型。确认后应同步更新本文及实际部署模板。
