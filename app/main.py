import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
import uuid
import json
from fastapi.concurrency import run_in_threadpool # 异步执行同步代码的关键

# 从 product_analyzer.py 导入核心函数 (注意：没有 'app.' 前缀)
from .product_analyzer import find_and_verify_product_urls, generate_product_jsonl

# 初始化 FastAPI 应用
app = FastAPI(title="商品分析API", description="上传商品图片，返回商品信息和相关URL")

# 创建一个临时目录来存放上传的图片
TEMP_IMAGE_DIR = "temp_images"
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

@app.post("/analyze-product/", tags=["Product Analysis"])
async def analyze_product_endpoint(images: List[UploadFile] = File(...)):
    """
    接收上传的商品图片，执行分析并返回结果。

    - **images**: 一个或多个图片文件。
    """
    if not images:
        raise HTTPException(status_code=400, detail="没有提供任何图片文件。")

    # 为这次请求创建一个唯一的子目录，防止多用户同时请求时文件冲突
    request_id = str(uuid.uuid4())
    request_dir = os.path.join(TEMP_IMAGE_DIR, request_id)
    os.makedirs(request_dir)

    image_paths = []
    try:
        # 1. 将上传的图片保存到临时文件夹
        for image in images:
            file_path = os.path.join(request_dir, image.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            image_paths.append(file_path)

        # 2. 【性能优化】在线程池中运行耗时的同步函数，防止阻塞服务器
        verified_urls = await run_in_threadpool(find_and_verify_product_urls, image_paths, max_results=1)
        
        if not verified_urls:
            raise HTTPException(status_code=404, detail="无法找到或验证任何可靠的商品页面。")

        urls_as_string = "\n".join(verified_urls)

        # 3. 【性能优化】同样，在线程池中运行这个耗时的函数
        product_jsonl_string = await run_in_threadpool(generate_product_jsonl, image_paths, urls_as_string)

        if not product_jsonl_string:
            raise HTTPException(status_code=500, detail="分析图片并生成JSONL时发生内部错误。")
            
        # 将返回的JSONL字符串解析为Python字典，以便API返回一个标准的JSON对象
        product_data = json.loads(product_jsonl_string)

        # 4. 返回成功的结果
        return {
            "message": "分析成功",
            "verified_urls": verified_urls,
            "product_data": product_data
        }
    except Exception as e:
        # 记录详细的错误日志，方便调试
        print(f"一个未处理的错误发生: {e}")
        raise HTTPException(status_code=500, detail=f"处理过程中发生未知错误: {str(e)}")
    finally:
        # 5. 清理本次请求产生的临时文件
        if os.path.exists(request_dir):
            shutil.rmtree(request_dir)

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "欢迎使用商品分析API"}