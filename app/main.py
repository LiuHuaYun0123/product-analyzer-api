# app/main.py (最终、最强、带CORS的版本)

import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
import uuid
from fastapi.concurrency import run_in_threadpool
# 1. 导入我们需要的CORS中间件
from fastapi.middleware.cors import CORSMiddleware

# 导入我们的分析函数
from .product_analyzer import analyze_images_only

app = FastAPI(
    title="商品图片分析API (最终版)", 
    description="使用最新的 google-generativeai 库并已启用CORS"
)

# 2. 添加CORS中间件配置
#    这是解决 "Failed to fetch" 问题的关键
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许来自任何来源的访问
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法 (GET, POST, etc.)
    allow_headers=["*"],  # 允许所有HTTP请求头
)


TEMP_IMAGE_DIR = "temp_images"
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

@app.post("/analyze/", tags=["Image Analysis"])
async def analyze_endpoint(images: List[UploadFile] = File(...)):
    if not images:
        raise HTTPException(status_code=400, detail="没有提供任何图片文件。")

    request_id = str(uuid.uuid4())
    request_dir = os.path.join(TEMP_IMAGE_DIR, request_id)
    os.makedirs(request_dir)

    image_paths = []
    try:
        for image in images:
            file_path = os.path.join(request_dir, image.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            image_paths.append(file_path)

        analysis_result = await run_in_threadpool(analyze_images_only, image_paths)
        
        if not analysis_result:
            raise HTTPException(status_code=500, detail="图片分析失败，无法从Gemini获取有效数据。")

        return {
            "message": "图片分析成功",
            "product_data": analysis_result
        }
    except Exception as e:
        print(f"一个未处理的错误发生: {e}")
        raise HTTPException(status_code=500, detail=f"处理过程中发生未知错误: {str(e)}")
    finally:
        if os.path.exists(request_dir):
            shutil.rmtree(request_dir)

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "欢迎使用最终版商品图片分析API"}