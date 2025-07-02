import os
import io
import json
import re
# 必要なライブラリをインポート
# pip install google-generativeai
import google.generativeai as genai
from google.generativeai.types import Tool, GenerationConfig
from google.generativeai import types
# =============================================================================
# ステップ 0: ここでAPIキーを設定します
# =============================================================================
# 下の行の "YOUR_GEMINI_API_KEY_HERE" を、あなた自身の実際のGemini APIキーに置き換えてください。
# キーは "AIzaSy..." で始まります。
API_KEY = "AIzaSyBeRAJv-EkYme20nOnmjYkSm9CnW5Z0mao" 

# --- APIキーの存在チェック ---
if API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    print("エラー：まずコード17行目の API_KEY 変数にあなたのGemini APIキーを設定してください。")
    exit()
genai.configure(api_key=API_KEY)


# =============================================================================
# メイン関数 (この関数を他のファイルから呼び出します)
# =============================================================================
def generate_product_jsonl(image_paths: list[str]) -> str:
    """
    複数の画像を受け取り、Geminiに内蔵されたGoogle検索ツールを使ってWebを検索させ、
    商品情報のJSONL文字列を生成して返す。

    Args:
        image_paths (list[str]): 分析したい画像のファイルパスのリスト。

    Returns:
        str: 抽出された商品情報のJSONL文字列。失敗した場合はNoneを返す。
    """
    print("\n--- 商品情報のJSONL生成タスクを開始します (Google検索ツール使用) ---")
    if not all(os.path.exists(p) for p in image_paths):
        print(f"❌ エラー: 指定された画像ファイルの一部が見つかりません: {image_paths}")
        return None
    
    # ステップ1: Geminiとツールの設定
    print("\n--- ステップ1: GeminiとGoogle検索ツールの準備 ---")
    # ツール使用には高性能なモデルを推奨
    model = genai.GenerativeModel(
        model_name='gemini-2.5-pro',
    )

    # ステップ2: プロンプトの組み立て (URLは不要)
    prompt = (
        "東京の天気はどうですか"

    )
    
    prompt_parts = [prompt]
    for path in image_paths:
        try:
            with open(path, 'rb') as f:
                prompt_parts.append({'mime_type': 'image/jpeg', 'data': f.read()})
            print(f"  - 画像 '{path}' を読み込みました。")
        except Exception as e:
            print(f"警告: 画像 '{path}' の読み込みに失敗しました: {e}")

    if len(prompt_parts) <= 1:
        print("エラー: 分析する有効な画像がありません。")
        return None

    try:
        # ステップ3: Geminiに画像とツールを渡して分析させる
        print("\n--- ステップ2: Geminiによる画像分析とWeb検索を開始します ---")
        generation_config = GenerationConfig(temperature=0.1)
        
        # model.generate_contentにツールを渡す
        response = model.generate_content(
            prompt_parts, 
            generation_config=generation_config
        )
        
        # 応答からJSONL部分だけを抽出する
        text_response = response.text
        jsonl_match = re.search(r'\{.*\}', text_response)
        if not jsonl_match:
            print(f"❌ Geminiからの応答に有効なJSONが含まれていませんでした。応答内容: {text_response}")
            return None

        jsonl_string = jsonl_match.group(0)
        
        # JSONとして有効か検証
        json.loads(jsonl_string) 

        print("\n✅ 分析完了。")
        return jsonl_string

    except Exception as e:
        print(f"❌ Gemini APIの処理中にエラーが発生しました: {e}")
        return None


# =============================================================================
# このスクリプトを直接実行した場合のテストコード
# =============================================================================
if __name__ == '__main__':
    print("--- スクリプトを単体でテスト実行します ---")
    
    # テスト用の画像パスを指定 (URLは不要になった)
    test_image_paths = ["12.jpg"]
    
    # メイン関数を呼び出し、結果を取得
    product_jsonl = generate_product_jsonl(test_image_paths)

    # 最終結果の表示
    if product_jsonl:
        print("\n\n✅✅✅【生成されたJSONL】✅✅✅")
        print(product_jsonl)
    else:
        print("\n\n❌【生成失敗】商品情報のJSONLを生成できませんでした。")

