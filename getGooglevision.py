import os
import io
import json
import re
# Gemini APIライブラリをインストールしてください:
# pip install google-generativeai
import google.generativeai as genai

# =============================================================================
# ステップ 0: ここでAPIキーを設定します
# =============================================================================
# 下の行の "YOUR_GEMINI_API_KEY_HERE" を、あなた自身の実際のGemini APIキーに置き換えてください。
# キーは "AIzaSy..." で始まります。
API_KEY = "AIzaSyBeRAJv-EkYme20nOnmjYkSm9CnW5Z0mao" 

# --- APIキーの存在チェック ---
if API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    print("エラー：まずコード15行目の API_KEY 変数にあなたのGemini APIキーを設定してください。")
    exit()
genai.configure(api_key=API_KEY)


# =============================================================================
# メイン関数 (この関数を他のファイルから呼び出します)
# =============================================================================
def generate_product_jsonl(image_paths: list[str], url: str) -> str:
    """
    複数の画像と商品ページのURLを受け取り、Gemini APIを使って分析し、
    商品情報のJSONL文字列を生成して返す。

    Args:
        image_paths (list[str]): 分析したい画像のファイルパスのリスト。
        url (str): 商品ページのURL。

    Returns:
        str: 抽出された商品情報のJSONL文字列。失敗した場合はNoneを返す。
    """
    print("\n--- 商品情報のJSONL生成タスクを開始します ---")
    if not all(os.path.exists(p) for p in image_paths):
        print(f"❌ エラー: 指定された画像ファイルの一部が見つかりません: {image_paths}")
        return None
    
    # ステップ1: Geminiに画像とURLテキストを渡して分析させる
    print("\n--- ステップ1: Geminiによる画像とURLの総合分析を開始します ---")
    model = genai.GenerativeModel('gemini-2.5-pro') # 高精度な分析のために1.5 Proを使用

    # プロンプトの組み立て
    prompt = (
        "You are a meticulous data extraction bot. Your task is to analyze the provided product images and the product page URL. "
        "Based on all this information, extract the required product attributes and format them as a single line of a JSONL object. "
        "The JSON keys must be in Japanese.\n"
        "Required keys: '商品名', 'ブランド', '色', '素材', 'サイズ', '金具', '品番'.\n"
        "For the '品番' (model number), find the official model number. If it's not explicitly mentioned, infer it from the context or state '不明'.\n"
        "For 'サイズ' (size), if not available, state '不明'.\n"
        "Example output:\n"
        "{\"商品名\": \"GGマーモント ミニ バケットバッグ\", \"ブランド\": \"グッチ\", \"色\": \"レッド\", \"素材\": \"レザー\", \"サイズ\": \"幅19cm x 高さ17cm x マチ11cm\", \"金具\": \"ゴールドトーン\", \"品番\": \"575163 DTDRT 6433\"}\n\n"
        "Here is the product page URL for context:\n"
        f"{url}\n\n"
        "Now, analyze the following images and generate the JSONL string:"
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
        # より一貫した結果を得るためにtemperatureを設定
        generation_config = genai.types.GenerationConfig(temperature=0.1)
        
        response = model.generate_content(prompt_parts, generation_config=generation_config)
        
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
        print(f"❌ Gemini APIの処理中またはJSONの解析中にエラーが発生しました: {e}")
        return None


# =============================================================================
# このスクリプトを直接実行した場合のテストコード
# =============================================================================
if __name__ == '__main__':
    print("--- スクリプトを単体でテスト実行します ---")
    
    # テスト用の画像パスとURLを指定
    test_image_paths = ["12.jpg"]
    test_url = """"""
    
    # メイン関数を呼び出し、結果を取得
    product_jsonl = generate_product_jsonl(test_image_paths, test_url)

    # 最終結果の表示
    if product_jsonl:
        print("\n\n✅✅✅【生成されたJSONL】✅✅✅")
        print(product_jsonl)
    else:
        print("\n\n❌【生成失敗】商品情報のJSONLを生成できませんでした。")

