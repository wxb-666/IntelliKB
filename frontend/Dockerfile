FROM node:22-alpine

# 前端开发容器工作目录
WORKDIR /app

# 先复制依赖清单，便于 Docker 复用依赖安装缓存。
COPY package.json package-lock.json ./
RUN npm ci

# 复制前端源码。
COPY . .

# Vite 开发服务端口。
EXPOSE 5173

# 监听 0.0.0.0，确保宿主机浏览器可以访问容器内的 Vite 服务。
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
