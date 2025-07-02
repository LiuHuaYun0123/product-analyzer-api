import requests
from bs4 import BeautifulSoup
import os
import io
import time
import json
import re
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from googlesearch import search
import google.generativeai as genai

# =============================================================================
# 步骤 0: 在这里配置您的API密钥
# =============================================================================
# 根据您的要求，我们暂时将密钥保留在代码中
API_KEY = "AIzaSyBeRAJv-EkYme20nOnmjYkSm9CnW5Z0mao" 

# --- APIキーの存在チェック ---
if API_KEY == "YOUR_GEMINI_API_KEY_HERE" or not API_KEY:
    print("错误：请先在代码第17行的 API_KEY 变量中设置您的Gemini API密钥。")
    exit()
genai.configure(api_key=API_KEY)


# -----------------------------------------------------------------------------
# 内部ヘルパー関数
# -----------------------------------------------------------------------------
def _get_product_details_from_gemini(image_paths: list[str]) -> (str, dict):
    """
    (内部関数) Gemini Pro Visionモデルを使い、複数の画像から詳細な説明と構造化されたキーワードを生成する。
    """
    print("\n--- ステップ1: Geminiによる画像の詳細分析を開始します ---")
    
    # 使用 gemini-1.5-flash 模型
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
            with open(path, 'rb') as f: image_parts.append({'mime_type': 'image/jpeg', 'data': f.read()})
            print(f"   - 画像 '{path}' を読み込みました。")
        except Exception as e:
            print(f"警告: 画像 '{path}' の読み込みに失敗しました: {e}")
            continue
    if not image_parts: return None, None
    
    final_prompt = prompt_parts + image_parts
    try:
        response = model.generate_content(final_prompt)
        text_response = response.text
        json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
        if not json_match: raise ValueError("応答から有効なJSONオブジェクトが見つかりませんでした。")
        
        json_string = json_match.group(0)
        description = text_response.replace(json_string, '').replace("```json", "").replace("```", "").strip()
        structured_data = json.loads(json_string)
        
        print(f"   - Geminiによる説明: {description}")
        print(f"   - 抽出された構造化データ: {structured_data}")
        return description, structured_data
    except Exception as e:
        print(f"❌ Gemini APIの処理中にエラーが発生しました: {e}")
        return None, None

def _find_candidate_urls(query: str, num_results: int = 10) -> list[str]:
    """(内部関数) 与えられたクエリでGoogle検索を行う。"""
    print(f"\n--- ステップ2: 詳細なクエリでWeb検索を開始します ---")
    print(f"   - 検索クエリ: {query}")
    try:
        urls = list(search(query, num=num_results, lang="ja"))
        print(f"   -> {len(urls)}件の候補URLが見つかりました。")
        return urls
    except Exception as e:
        print(f"❌ Google検索中にエラーが発生しました: {e}")
        return []

# 这是全新的、轻量化的验证函数
def _verify_page_is_product_page(url: str, required_info: dict) -> bool:
    """
    (轻量版) 使用requests和BeautifulSoup访问URL，只验证核心关键词。
    """
    print(f"   [検証中] -> (軽量版) サイトを訪問して内容を確認: {url}")

    # 伪装成浏览器，防止被一些网站屏蔽
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # 发送HTTP请求，设置15秒超时
        response = requests.get(url, headers=headers, timeout=15)
        # 如果请求不成功（比如404 Not Found），则直接判定为失败
        if response.status_code != 200:
            print(f"     -> ❌ 確認失敗: HTTPステータスコードが {response.status_code} でした。")
            return False

        # 使用BeautifulSoup解析HTML内容
        soup = BeautifulSoup(response.text, 'html.parser')
        body_text = soup.get_text().lower()

        # 我们只检查核心关键词，因为电商信号可能由JS加载，我们看不到
        required_keywords = [
            required_info.get('brand','').lower(), 
            required_info.get('product_name','').lower().split()[0]
        ]
        required_keywords.extend([f.lower() for f in required_info.get('features', [])])
        required_keywords = [kw for kw in required_keywords if kw]

        # 检查所有必需的关键词是否都出现在页面文本中
        # （这里使用 all，比之前的 any 更严格，以弥补没有电商信号检查的不足）
        found_all_required = all(keyword in body_text for keyword in required_keywords)

        if found_all_required:
            print(f"     -> ✔️ 確認完了: (軽量版) このページは関連性が高いページです。")
            return True
        else:
            print(f"     -> ❌ 確認失敗: (軽量版) 必須キーワードが不足しています。")
            return False

    except requests.exceptions.RequestException as e:
        # 处理网络请求相关的各种异常
        print(f"     -> ❌ 検証中にネットワークエラーが発生しました: {e}")
        return False
    except Exception as e:
        # 处理其他未知异常
        print(f"     -> ❌ 検証中に未知のエラーが発生しました: {e}")
        return False

def find_and_verify_product_urls(image_paths: list[str], max_results: int = 3) -> list[str]:
    """
    複数の画像パスを受け取り、AI分析とWeb検証を通じて、信頼できる商品ページのURLリストを返す。
    """
    if not all(os.path.exists(p) for p in image_paths):
        print(f"❌ エラー: 指定された画像ファイルの一部が見つかりません: {image_paths}")
        return []

    description, product_info = _get_product_details_from_gemini(image_paths)
    
    verified_urls = []
    if description and product_info:
        search_query = f"{product_info.get('brand', '')} {product_info.get('product_name', '')} {description}"
        candidate_urls = _find_candidate_urls(search_query)
        
        unique_domains = {}
        for url in candidate_urls:
            try:
                domain = urlparse(url).netloc
                if domain not in unique_domains:
                    unique_domains[domain] = url
            except Exception:
                continue
        
        filtered_candidates = list(unique_domains.values())

        if filtered_candidates:
            print(f"\n--- ステップ3: 上位{len(filtered_candidates)}件のユニークなドメイン候補を詳細検証します ---")
            for url in filtered_candidates:
                if _verify_page_is_product_page(url, product_info):
                    verified_urls.append(url)
                if len(verified_urls) >= max_results:
                    break
    
    return verified_urls

def generate_product_jsonl(image_paths: list[str], url: str) -> str:
    """
    複数の画像と商品ページのURLを受け取り、Gemini APIを使って分析し、商品情報のJSONL文字列を生成して返す。
    """
    print("\n--- 商品情報のJSONL生成タスクを開始します ---")
    if not all(os.path.exists(p) for p in image_paths):
        print(f"❌ エラー: 指定された画像ファイルの一部が見つかりません: {image_paths}")
        return None
    
    print("\n--- ステップ1: Geminiによる画像とURLの総合分析を開始します ---")
    # 使用 gemini-1.5-pro 模型
    model = genai.GenerativeModel('gemini-1.5-pro')

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
            print(f"   - 画像 '{path}' を読み込みました。")
        except Exception as e:
            print(f"警告: 画像 '{path}' の読み込みに失敗しました: {e}")

    if len(prompt_parts) <= 1:
        print("エラー: 分析する有効な画像がありません。")
        return None

    try:
        generation_config = genai.types.GenerationConfig(temperature=0.1)
        response = model.generate_content(prompt_parts, generation_config=generation_config)
        
        text_response = response.text
        jsonl_match = re.search(r'\{.*\}', text_response, re.DOTALL)
        if not jsonl_match:
            print(f"❌ Geminiからの応答に有効なJSONが含まれていませんでした。応答内容: {text_response}")
            return None

        jsonl_string = jsonl_match.group(0)
        json.loads(jsonl_string) 

        print("\n✅ 分析完了。")
        return jsonl_string
    except Exception as e:
        print(f"❌ Gemini APIの処理中またはJSONの解析中にエラーが発生しました: {e}")
        return None