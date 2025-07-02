import requests
import json
import extruct
import jsonlines
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from w3lib.html import get_base_url
import time
import re  # ✅ 新增导入

# === 配置 Google CSE ===
API_KEY = 'AIzaSyDqwdySk1md1n3NfnYLwhA5GYgBoSoLjUI'
CX = 'd7a2a5fa7357f49ad'

def google_image_search(query, total_results=30, site_domains=None):
    """
    扩展版 Google 图片搜索：支持分页和指定站点。
    返回总共最多 10 条结果。
    """
    results = []
    base_url = "https://www.googleapis.com/customsearch/v1"
    num_per_request = 10  # 每页最大请求数（Google限制）
    domain_list = site_domains or [None]  # 如果没传site_domains，则跑全网搜索

    for domain in domain_list:
        for start in range(1, total_results + 1, num_per_request):
            if len(results) >= 10:  # ✅ 限制总共返回最多 10 条
                return results

            params = {
                'key': API_KEY,
                'cx': CX,
                'searchType': 'image',
                'q': query,
                'num': num_per_request,
                'start': start
            }
            if domain:
                params['siteSearch'] = domain
                params['siteSearchFilter'] = 'i'  # include

            try:
                response = requests.get(base_url, params=params, timeout=10)
                data = response.json()

                for item in data.get('items', []):
                    if len(results) >= 10:  # ✅ 再次判断上限
                        return results
                    image_link = item['link']
                    context_link = item.get('image', {}).get('contextLink')
                    results.append({'image_url': image_link, 'source_url': context_link})

                time.sleep(1)  # 防止 API 封锁
            except Exception as e:
                print(f"⚠️ 请求失败: {e} (start={start}, site={domain})")
    return results

def extract_product_info(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        base_url = get_base_url(resp.text, resp.url)

        # --- 用 extruct 抽取结构化数据 ---
        metadata = extruct.extract(resp.text, base_url=base_url, syntaxes=['json-ld', 'microdata'], uniform=True)
        product = {}

        for item in metadata.get('json-ld', []):
            if isinstance(item, dict) and item.get('@type') == 'Product':
                product['商品名'] = item.get('name')
                brand = item.get('brand')
                if isinstance(brand, dict):
                    product['ブランド'] = brand.get('name')
                else:
                    product['ブランド'] = brand
                product['色'] = item.get('color')
                product['素材'] = item.get('material')
                product['サイズ'] = item.get('size')
                product['品番'] = item.get('sku') or item.get('mpn')
                break  # 只取第一个 Product

        # --- 如果结构化数据不全，尝试从 HTML 中提取 ---
        soup = BeautifulSoup(resp.text, 'lxml')

        def find_in_text(patterns):
            """
            精准提取格式为「キー: 値」或「キー：値」的字段，避免误抓公司信息等长文本。
            """
            for tag in soup.find_all(['li', 'td', 'th', 'p', 'span', 'div']):
                text = tag.get_text(strip=True)
                for key in patterns:
                    match = re.match(rf'^{re.escape(key)}\s*[:：]\s*(.+)$', text)
                    if match:
                        value = match.group(1).strip()
                        if len(value) > 100:
                            continue  # 忽略异常过长内容
                        return value
            return None

        if not product.get('商品名'):
            product['商品名'] = soup.title.string.strip() if soup.title else None

        if not product.get('ブランド'):
            product['ブランド'] = find_in_text(['ブランド', 'ブランド名', 'Brand'])

        if not product.get('色'):
            product['色'] = find_in_text(['カラー', '色', 'Color'])

        if not product.get('素材'):
            product['素材'] = find_in_text(['素材', 'Material'])

        if not product.get('サイズ'):
            product['サイズ'] = find_in_text(['サイズ', 'Size'])

        if not product.get('金具'):
            product['金具'] = find_in_text(['金具', 'Hardware'])

        if not product.get('品番'):
            product['品番'] = find_in_text(['品番', '型番', 'SKU', '商品番号'])

        # ✅ 最后统一补全字段
        required_fields = ['商品名', 'ブランド', '色', '素材', 'サイズ', '金具', '品番']
        for field in required_fields:
            if field not in product or product[field] is None:
                product[field] = "null"

        return product

    except Exception as e:
        return {'error': str(e)}

def main():
    queries = [
        "SALE 美品 GUCCI グッチ フローラ クリアバッグ 548713 レディース トートバッグ",
    ]

    site_list = [
        None,
        "www.buyma.com",
        "www.farfetch.com",
        "item.rakuten.co.jp",
        "www.yoox.com",
    ]

    with jsonlines.open('results.jsonl', mode='w') as writer:
        for query in queries:
            print(f"🔍 検索: {query}")
            try:
                search_results = google_image_search(query, total_results=30, site_domains=site_list)
                print(f"📸 找到图片数量: {len(search_results)}")
                for result in search_results:
                    source_url = result.get('source_url')
                    if not source_url:
                        print("⚠️ 缺少 source_url，跳过")
                        continue
                    print(f"  🌐 取得中: {source_url}")
                    info = extract_product_info(source_url)
                    print("✅ 抽取结果:", info)
                    writer.write({
                        'query': query,
                        'image_url': result['image_url'],
                        'source_url': source_url,
                        'product_info': info
                    })
                    time.sleep(1)
            except Exception as e:
                print(f"❌ 搜索或写入错误: {e}")


if __name__ == "__main__":
    main()
