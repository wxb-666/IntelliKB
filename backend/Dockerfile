FROM python:3.11-slim

# 禁止将.py编译为.pyc
ENV PYTHONDONTWRITEBYTECODE=1
# 禁用python的输出缓冲
ENV PYTHONUNBUFFERED=1
# 不留依赖的压缩包缓存，减少docker镜像体积
ENV PIP_NO_CACHE_DIR=1

# 工作目录，相当于在容器中执行 mkdir -p /app && cd /app
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码到容器
COPY app ./app

# 声明后端容器端口为8000
EXPOSE 8000

# 容器启动时执行的命令（但在正式环境中就要去掉热重载）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]