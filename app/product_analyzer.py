from google import genai
from google.genai import types
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import json
import re

# API密钥配置保持不变
API_KEY = "AIzaSyBeRAJv-EkYme20nOnmjYkSm9CnW5Z0mao"
if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    print("错误：请先设置您的Gemini API密钥。")
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
    (最终版) 调用Gemini分析图片，并返回结构化数据。
    """
    print("\n--- (最终版) 开始Gemini图片分析 ---")
    
    # Prompt也完全相同
    prompt_parts = [
        "You are a professional luxury goods authenticator and data analyst. "
        "Analyze the following images of a product and provide two things in your response in Japanese:\n"
        "1. A detailed one-paragraph description of the product, including brand, product name/line, material, color, and key features.\n"
        "2. A JSON object containing the key attributes. The keys for the JSON object must be: 'brand', 'product_name', 'material', 'color', 'features' (as a list of strings).\n"
        "Example JSON: {\"brand\": \"グッチ\", \"product_name\": \"GGリボン ハーバリウム トートバッグ\", \"material\": \"GGスプリーム キャンバス\", \"color\": \"ベージュ/エボニー/ピンク\", \"features\": [\"日本限定\", \"花柄\", \"レザートリム\"]}\n"
        "Provide only the description paragraph and the JSON object, with nothing else before or after.\n\n"
        "Images to analyze:\n"
    ]
    
    image_parts = []
    my_file = client.files.upload(file=image_paths[0])  # 假设只分析第一张图片
    for path in image_paths:
        try:
            # 在Python 3.9+中，可以直接读取文件为PIL Image对象，新库更推荐这种方式
            # 但为了保持简单，我们继续使用原来的字节流方式，它同样兼容
            with open(path, 'rb') as f:
                image_parts.append({'mime_type': 'image/jpeg', 'data': f.read()})
            print(f"   - 图像 '{path}' 已加载。")
        except Exception as e:
            print(f"警告: 无法加载图片 '{path}': {e}")
            continue
            
    if not image_parts:
        print("错误：没有有效的图片可供分析。")
        return None
    
    final_prompt = prompt_parts + image_parts
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=[my_file,final_prompt],
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
            print("❌ Gemini返回的内容中未找到有效的JSON对象。")
            return None
        
        json_string = json_match.group(0)
        structured_data = json.loads(json_string)
        
        print(f"   - Gemini分析完成。")
        return structured_data

    except Exception as e:
        print(f"❌ Gemini API处理过程中发生错误: {e}")
        return None