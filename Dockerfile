# Dockerfile (极简版)

# 使用和您本地匹配的Python 3.10版本
FROM python:3.10-slim

# 设置一个环境变量，让日志能即时显示
ENV PYTHONUNBUFFERED 1

# 在容器内创建一个叫 /code 的工作目录
WORKDIR /code

# 复制依赖文件并安装
# (我们稍后会更新 requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 将我们本地的整个 app 文件夹，复制到容器的 /code 目录里
COPY ./app ./app

# 暴露端口
EXPOSE 8000

# 启动应用的命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]