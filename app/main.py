import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
import uuid
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

# product_analyzerを導入
from app.product_analyzer import analyze_images_only

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI(
    title="商品画像解析API（最終版）", 
    description="最新の google-generativeai ライブラリを使用し、CORSを有効化しています。"
)

# CORSミドルウェアを追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dun-three.vercel.app"],# 特定のオリジンからのリクエストを許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

# フロントエンドからアップロードされた複数の画像を保存するためのフォルダを作成
TEMP_IMAGE_DIR = "temp_images"
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

# 複数の画像ファイルを受け取り、解析結果を返す
@app.post("/analyze/", tags=["Image Analysis"])
async def analyze_endpoint(images: List[UploadFile] = File(...)):
    # 画像がアップロードされていない場合、エラーを返す
    if not images:
        raise HTTPException(status_code=400, detail="画像ファイルをご提供ください。")

    # 一時ディレクトリを作成し、アップロードされた画像を保存
    request_id = str(uuid.uuid4())
    request_dir = os.path.join(TEMP_IMAGE_DIR, request_id)
    os.makedirs(request_dir)
    
    image_paths = []
    try:
        # 画像を保存
        for image in images:
            file_path = os.path.join(request_dir, image.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            image_paths.append(file_path)

        # 画像解析を実行
        analysis_result = await run_in_threadpool(analyze_images_only, image_paths)
        
        if not analysis_result:
            raise HTTPException(status_code=500, detail="画像解析に失敗しました。Geminiから有効なデータを取得できませんでした。")

        return {
            "message": "画像解析に成功しました。",
            "product_data": analysis_result
        }
    except Exception as e:
        print(f"未処理のエラーが発生しました: {e}")
        raise HTTPException(status_code=500, detail=f"処理中に予期しないエラーが発生しました: {str(e)}")
    finally:
        if os.path.exists(request_dir):
            shutil.rmtree(request_dir)

# サーバーの健康状態を確認するためのエンドポイント。サーバーの正常稼働を確認するための簡単なメッセージを返す
@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "最終版商品画像解析APIへようこそ"}