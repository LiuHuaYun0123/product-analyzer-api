# app/product_analyzer.py (极简版)

import os
import json
import re
import google.generativeai as genai

# API密钥配置保持不变
API_KEY = "AIzaSyBeRAJv-EkYme20nOnmjYkSm9CnW5Z0mao" 
if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    print("错误：请先设置您的Gemini API密钥。")
    exit()
genai.configure(api_key=API_KEY)

def analyze_images_only(image_paths: list[str]) -> dict:
    """
    (极简版) 只调用Gemini分析图片，并返回结构化数据。
    不再进行任何网络搜索或页面验证。
    """
    print("\n--- (极简版) 开始Gemini图片分析 ---")
    
    # 依然使用 gemini-1.5-flash 模型以保证速度
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Prompt保持不变，因为我们仍然希望Gemini返回同样格式的数据
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
    for path in image_paths:
        try:
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
        response = model.generate_content(final_prompt)
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