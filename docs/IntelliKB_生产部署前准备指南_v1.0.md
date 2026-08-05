# IntelliKB 生产部署前准备指南

<table>
  <thead><tr><th>项目</th><th>内容</th></tr></thead>
  <tbody>
    <tr><td>文档版本</td><td>V1.0</td></tr>
    <tr><td>适用对象</td><td>在 Windows 本地开发，计划部署 IntelliKB 至服务器的人员</td></tr>
    <tr><td>本次目标</td><td>完成本机 Git 与 Docker、GitHub 私有仓库及 GHCR 镜像发布准备</td></tr>
  </tbody>
</table>

---

## 1. 交付链路

本地电脑与服务器不共享运行中的容器。正确流程如下：

```text
本地代码和 Docker 配置
          |
          v
GitHub 私有代码仓库
          |
          v
本地或 GitHub Actions 构建镜像
          |
          v
GitHub Container Registry（GHCR）
          |
          v
服务器拉取镜像并创建自己的容器
```

GitHub 代码仓库存放代码与环境定义文件；GHCR 存放构建完成的 Docker 镜像；服务器实际运行容器并保存生产数据、密钥与备份。

## 2. 今日完成清单

- [ ] 可登录 GitHub 账号，且已验证邮箱。
- [ ] 安装 Git，并配置姓名和邮箱。
- [ ] 安装并启动 Docker Desktop，确认 Docker Compose 可用。
- [ ] 创建 IntelliKB 私有代码仓库。
- [ ] 将当前项目首次推送到 GitHub。
- [ ] 创建 `.gitignore` 与 `.env.example`，确保密钥不会上传。
- [ ] 确定 GHCR 镜像发布方式。

## 3. GitHub 账号与代码仓库

### 3.1 账号准备

打开 [GitHub](https://github.com/) 并登录或注册账号。建议在 Settings 中验证邮箱并开启双重验证。不要把 GitHub 密码、访问令牌、模型 API Key 或服务器密码写进项目文件。

### 3.2 创建私有仓库

1. 点击 GitHub 右上角的 `+`，选择 `New repository`。
2. Repository name 填写 `IntelliKB`。
3. 选择 `Private`。
4. 当前本地已有项目文件时，不勾选 `Add a README file`、`.gitignore` 或 License。
5. 点击 `Create repository`，保留仓库地址，例如：

```text
https://github.com/你的GitHub用户名/IntelliKB.git
```

## 4. 安装和配置 Git

从 [Git for Windows](https://git-scm.com/download/win) 下载并安装。安装时大部分选项保持默认，并允许从 PowerShell 使用 Git。

安装后重新打开 PowerShell，执行：

```powershell
git --version
```

显示版本号后，将下方内容替换为你的姓名和 GitHub 注册邮箱再执行：

```powershell
git config --global user.name "你的姓名或昵称"
git config --global user.email "你的GitHub注册邮箱"
git config --global init.defaultBranch main
git config --global --list
```

## 5. 安装 Docker Desktop

### 5.1 安装

从 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 下载并安装。电脑建议至少 8 GB 内存，推荐 16 GB；安装程序若提示启用 WSL 2 或 Virtual Machine Platform，请按提示启用并重启。

启动 Docker Desktop，等待状态显示为 Running。然后在新的 PowerShell 窗口执行：

```powershell
docker --version
docker compose version
docker run --rm hello-world
```

前两条命令显示版本号，第三条命令显示欢迎信息，代表 Docker 可正常拉取并运行容器。

### 5.2 建议设置

- 使用 WSL 2 based engine。
- 为 Docker 分配至少 4 个 CPU、8 GB 内存、40 GB 磁盘；电脑资源充足时建议 6 至 8 个 CPU、12 GB 以上内存。
- Docker 数据目录不要放入 OneDrive 等同步目录。
- 项目保留在本机磁盘，例如 `C:\Users\TAT\Desktop\IntelliKB`。

## 6. 推送当前项目到 GitHub

### 6.1 创建 `.gitignore`

在项目根目录创建 `.gitignore`，至少包含：

```gitignore
# 环境变量和密钥
.env
.env.*
!.env.example
*.pem
*.key

# 运行数据
data/
backups/
logs/

# 构建产物
__pycache__/
*.pyc
node_modules/
dist/
build/

# IDE 和系统文件
.idea/
.vscode/
.DS_Store
Thumbs.db
```

真实 API Key、数据库密码、服务器 IP、TLS 证书与生产备份不能提交到 GitHub。项目中仅提交 `.env.example`，用于列出变量名称而不填写真实值。

### 6.2 初始化与首次推送

在 IntelliKB 项目根目录执行。将仓库地址替换为第 3 步创建的真实地址：

```powershell
git init
git add .
git commit -m "chore: initialize IntelliKB project"
git branch -M main
git remote add origin https://github.com/你的GitHub用户名/IntelliKB.git
git push -u origin main
```

首次推送时，GitHub 可能要求在浏览器登录授权，或输入 Personal Access Token。请使用浏览器授权或 Token，不使用 GitHub 账户密码。

## 7. 准备 GitHub Container Registry（GHCR）

GHCR 是 GitHub 的 Docker 镜像仓库。无需手动创建空镜像仓库，第一次推送镜像时会自动创建对应的 Package。

后续镜像地址示例：

```text
ghcr.io/你的GitHub用户名/intellikb-api:0.1.0
ghcr.io/你的GitHub用户名/intellikb-web:0.1.0
```

### 7.1 推荐方式：GitHub Actions 自动发布

后续添加 GitHub Actions 工作流，在代码推送到 `main` 或发布版本时自动构建并推送镜像。工作流最小权限为：

```yaml
permissions:
  contents: read
  packages: write
```

这种方式不需要在本地长期保存 GHCR 发布令牌，适合作为正式流程。

### 7.2 临时方式：本地手动推送

在 GitHub Settings -> Developer settings -> Personal access tokens 中创建 Classic Token，授予 `write:packages` 与 `read:packages`；私有仓库通常还需要 `repo` 权限。令牌只显示一次，应保存在密码管理器中。

有实际镜像后，登录与推送示例：

```powershell
docker login ghcr.io -u 你的GitHub用户名
docker tag intellikb-api:0.1.0 ghcr.io/你的GitHub用户名/intellikb-api:0.1.0
docker push ghcr.io/你的GitHub用户名/intellikb-api:0.1.0
```

登录时输入 Token 作为密码，不输入 GitHub 账户密码。没有应用镜像前不需要执行这一步。

## 8. 今日验收

<table>
  <thead><tr><th>检查项</th><th>完成标准</th></tr></thead>
  <tbody>
    <tr><td>Git</td><td><code>git --version</code> 能输出版本号，且已配置姓名和邮箱。</td></tr>
    <tr><td>Docker</td><td><code>docker run --rm hello-world</code> 成功结束。</td></tr>
    <tr><td>GitHub</td><td>存在 IntelliKB 私有仓库，网页中能看到本地项目文件。</td></tr>
    <tr><td>安全</td><td><code>.env</code>、Token、证书和备份不被 Git 跟踪。</td></tr>
    <tr><td>GHCR</td><td>已确定使用 GitHub Actions 自动发布，或已创建最小权限的临时 Token。</td></tr>
  </tbody>
</table>

## 9. 完成后的下一步

1. 创建前端、后端的 Dockerfile 与 `compose.yaml`。
2. 在本机启动 PostgreSQL + PGVector、MongoDB、Redis、MinIO、前后端等完整环境。
3. 添加 GitHub Actions，自动构建并发布 GHCR 镜像。
4. 准备服务器、域名、HTTPS、生产 `.env`、数据卷和备份策略。
5. 服务器从 GHCR 拉取镜像，以 Docker Compose 部署。
