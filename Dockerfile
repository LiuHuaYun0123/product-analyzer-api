# 使用和您本地匹配的Python 3.10版本
FROM python:3.10-slim

# 设置一个环境变量，告诉Python输出是无缓冲的，日志能即时显示
ENV PYTHONUNBUFFERED 1

# --- 安装系统依赖 (为Selenium安装Chrome) ---
# 这一部分保持不变
RUN apt-get update && apt-get install -y \
    wget gnupg --no-install-recommends \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# --- 配置应用环境 (★这里有重要修改★) ---
# 1. 在容器内创建一个叫 /code 的工作目录
WORKDIR /code

# 2. 先只复制依赖文件，这样可以利用Docker缓存，未来如果只改代码，就不需要重新安装所有库了
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. 再将我们本地的整个 app 文件夹，复制到容器的 /code 目录里
#    这样容器里的结构就是 /code/app/main.py
COPY ./app ./app

# --- 运行应用 (★这里有重要修改★) ---
# 暴露端口
EXPOSE 8000

# 容器启动时要执行的命令
# 我们从 /code 目录启动，并告诉uvicorn运行 app 包里的 main 模块的 app 实例
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]