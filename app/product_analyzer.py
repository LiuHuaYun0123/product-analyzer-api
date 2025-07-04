from google import genai
from google.genai import types
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import json
import re

# API密钥配置保持不变
API_KEY = "AIzaSyBeRAJv-EkYme20nOnmjYkSm9CnW5Z0mao"
if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    print("先にGemini APIキーを設定してください。")
    exit()
client = genai.Client(api_key=API_KEY)
google_search_tool = Tool(
    google_search = GoogleSearch()
)

my_generation_config = GenerateContentConfig(
    temperature=0.0,
    top_p=1.0,
    top_k=32,
    max_output_tokens=4096,
    stop_sequences=['}'] # 这是一个可选的高级技巧
)
def analyze_images_only(image_paths: list[str]) -> dict:
    """
    （最終版）Geminiを使用して画像を解析し、構造化データを返します。
    """
    print("\n--- （最終版）Gemini画像解析を開始します ---")
    
    # Prompt也完全相同
    prompt_parts = [
        "You are a professional luxury goods authenticator and data analyst. "
        "Analyze the following images of a product and provide two things in your response in Japanese:\n"
        # --- 変更点1：説明文にも品番/型番の要求を追加 ---
        "1. A detailed one-paragraph description of the product, including brand, product name/line, model number (品番/型番 if available), material, color, and key features.\n"
        # --- 変更点2：JSONオブジェクトのキーに`model_number`を追加 ---
        "2. A JSON object containing the key attributes. The keys for the JSON object must be: 'brand', 'product_name', 'model_number', 'material', 'color', 'features' (as a list of strings).\n"
        # --- 変更点3：JSONの例にも`model_number`を追加 ---
        "Example JSON: {\"brand\": \"グッチ\", \"product_name\": \"GGリボン ハーバリウム トートバッグ\", \"model_number\": \"415721 KLQHG 8526\", \"material\": \"GGスプリーム キャンバス\", \"color\": \"ベージュ/エボニー/ピンク\", \"features\": [\"日本限定\", \"花柄\", \"レザートリム\"]}\n"
        "Provide only the description paragraph and the JSON object, with nothing else before or after.\n\n"
        "Images to analyze:\n"
    ]
    
    my_file = []
    # my_file = client.files.upload(file=image_paths[0])  # 假设只分析第一张图片
    for path in image_paths:
        try:
            my_file_object = client.files.upload(file=path)
            my_file.append(my_file_object)
            print(f"   - 画像「{path}」を読み込みました。")
        except Exception as e:
            print(f"警告：画像「{path}」を読み込めませんでした：{e}")
            continue
            
    if not my_file:
        print("エラー：解析可能な有効な画像が見つかりませんでした。")
        return None
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents= my_file + [prompt_parts],
                # types.Part.from_bytes(
                #     data=image_bytes,
                #     mime_type='image/jpeg',
                # ),
            config=GenerateContentConfig(
                tools=[google_search_tool],
                temperature=0.0,
            )
        )
        text_response = response.text
        json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
        
        if not json_match:
            print("❌ Geminiの応答に有効なJSONオブジェクトが見つかりませんでした。")
            return None
        
        json_string = json_match.group(0)
        structured_data = json.loads(json_string)
        
        print(f"   - Geminiによる解析が完了しました。")
        print(f"   - 解析された構造化データ: {structured_data}")
        return structured_data

    except Exception as e:
        print(f"❌ Gemini APIの処理中にエラーが発生しました: {e}")
        return None