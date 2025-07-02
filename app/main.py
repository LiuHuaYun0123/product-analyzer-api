# app/main.py (极简版)

import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
import uuid
from fastapi.concurrency import run_in_threadpool

# 只导入我们唯一需要的分析函数
from .product_analyzer import analyze_images_only

app = FastAPI(title="商品图片分析API (极简版)", description="只接收图片，返回Gemini的分析结果")

TEMP_IMAGE_DIR = "temp_images"
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

@app.post("/analyze/", tags=["Image Analysis"])
async def analyze_endpoint(images: List[UploadFile] = File(...)):
    """
    接收上传的商品图片，执行Gemini分析并直接返回结果。
    """
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

        # 在线程池中运行我们的极简版分析函数
        analysis_result = await run_in_threadpool(analyze_images_only, image_paths)
        
        if not analysis_result:
            raise HTTPException(status_code=500, detail="图片分析失败，无法从Gemini获取有效数据。")

        # 直接返回成功的结果
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
    return {"status": "ok", "message": "欢迎使用极简版商品图片分析API"}