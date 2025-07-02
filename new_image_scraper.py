import os
import re
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------------------------------------------------------------
# ユーティリティ関数: テキストからURLを抽出する
# -----------------------------------------------------------------------------
def extract_urls_from_text(text: str) -> list[str]:
    """
    正規表現を使って、与えられたテキストブロックから全てのユニークなURLを抽出する。
    """
    # フォーマット [数字](URL) や (URL) に含まれるURLを検出する正規表現
    # http または https で始まる、')' または ',' で終わらない文字列にマッチ
    urls = re.findall(r'\(https?://[^\s,)]+\)', text)
    
    # 前後のカッコを取り除き、ユニークなURLのリストを作成する
    cleaned_urls = sorted(list(set([url.strip('()') for url in urls])))
    
    print(f"テキストから {len(cleaned_urls)} 個のユニークなURLを抽出しました。")
    return cleaned_urls

# -----------------------------------------------------------------------------
# 機能: 指定されたURLからJPG画像をダウンロードする (改良版)
# -----------------------------------------------------------------------------
def scrape_and_download_images(url: str, save_folder: str, num_images_to_download: int = 10):
    """
    Seleniumを使ってURLにアクセスし、JPG/JPEG形式の画像のみをダウンロードする。
    """
    if not url: return
    print(f"  [画像抽出中] -> {url}")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--log-level=3')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        time.sleep(5)
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # --- ★★★ 改良点: メインの商品画像コンテナを特定する ★★★ ---
        image_container = None
        # 一般的な商品ページの画像エリアで使われるセレクタをリスト化（具体的なものから順に試す）
        possible_selectors = [
            'div.product-gallery',
            'div.product__media-gallery',
            'div.product-images',
            'div#item-images',
            'main' # HTML5のmainタグ
        ]

        for selector in possible_selectors:
            # CSSセレクタを使って要素を探す
            container = soup.select_one(selector)
            if container:
                image_container = container
                print(f"    -> 主要な画像コンテナ ('{selector}') を発見。このエリア内を検索します。")
                break
        
        # 特定のコンテナが見つからなかった場合、最終手段としてページ全体を対象にする
        if not image_container:
            image_container = soup.body
            print(f"    -> 警告: 特定の画像コンテナが見つかりませんでした。ページ全体を検索します。")
        
        # ----------------------------------------------------------------

        if not os.path.exists(save_folder): os.makedirs(save_folder)
        
        # 特定したコンテナの中だけを検索する
        all_imgs = image_container.find_all('img')
        download_count = 0
        for img_tag in all_imgs:
            if download_count >= num_images_to_download: break
            img_url = img_tag.get('src')
            if not img_url or 'base64' in img_url or 'svg' in img_url: continue
            img_url = urljoin(url, img_url)
            path = urlparse(img_url).path
            if not (path.lower().endswith('.jpg') or path.lower().endswith('.jpeg')): continue
            try:
                img_response = requests.get(img_url, stream=True, timeout=10)
                if img_response.status_code == 200:
                    filename_base = os.path.basename(path)
                    safe_filename = "".join([c for c in filename_base if c.isalpha() or c.isdigit() or c in ('.', '_')]).rstrip()
                    if not safe_filename: safe_filename = f"image_{download_count+1}.jpg"
                    filepath = os.path.join(save_folder, safe_filename)
                    with open(filepath, 'wb') as f: f.write(img_response.content)
                    download_count += 1
            except Exception: continue
        print(f"    -> {download_count} 枚のJPG画像をダウンロード完了。")
    finally:
        driver.quit()

# =============================================================================
# 主プログラム
# =============================================================================
if __name__ == "__main__":
    
    # 1. リンクが混在したテキストをここに貼り付けます
    input_text = """
    これらのバッグは、グッチのGGモノグラムと、特徴的なパッチワークデザインが共
[1](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFyenfTMbR3uTU4MTYqQu0M0XaJY-PfL77eUUG-fiSXkS9Idw09pRwJPL0jCT1SMOYxpfZjGlXAMZXhlJdhwqfccDO59XrrIkj_YWKzprx0R7TWAMI-i0gg6mEM_AfZdEgZCzFX2-ZjJYYwO1sBgGQRKwdDeNmn6jN8tiCcQnmXD48okXX56MM=),
[2](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHFZNmr7emMz5kNZgN_-1bDabBVDP-ZJaLWV1axXOdQIVFOkeg93okDZ1bTwndSs77Y3lLkGiprl7OgmmHYYrJR5vGLdx8Ft1SE_bXNdREkWUzAkJGyo-HwIu3eD0Vyne91XWBYGNxyHaq8M74UUJpTZFiDxXT2SRujch5PQnrZaNn5Eg==),
[3](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHpWRHbkgVYf9qJnaGV0jcEnCKPH-xRrEZI1WC8hy44HYON4vtOXjOXPl6W1vlX2sjcxn9U7UWV6CPs6eZi75FbbqGtElIVi9uXPGhgzByw19Ueu2_cYe1uRBSf3OwwLj-KnKBu8PhpmNmcWNQzfG1qssxg0yX7xy335UmqfAvcaSUqgBTxiisPS4ADJyd-ckSHHYNH0yXr)通しています。特に「Sciroppo」というキーワードは、この特定のコレクションやデザインに関連付けられています。
[1](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFyenfTMbR3uTU4MTYqQu0M0XaJY-PfL77eUUG-fiSXkS9Idw09pRwJPL0jCT1SMOYxpfZjGlXAMZXhlJdhwqfccDO59XrrIkj_YWKzprx0R7TWAMI-i0gg6mEM_AfZdEgZCzFX2-ZjJYYwO1
[4](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE-dOEarwBq9A81OVNj8JsJ-JCZ9P1umxndqA-U7-cfplHZ9lXPdw79dZ4trYdW1Ha7kdblHlQ-uRPIvcXmaullqADfVLHG82fJz1Or42KQjC4ktLKrfiMxcKiT4mgZKzkGdANAl9IPfUvOp6E0TszhfWYAUpP20slL_fn-SG9iFKPfHv5qanf_wcSVJwnuyhPKZUt3xqAhXL-TI1SAuMwrqK7K6fXa7iYeEUg5tkRtEOo9s-B5p_KSk1uiyhtNpQ==)sBgGQRKwdDeNmn6jN8tiCcQnmXD48okXX56MM=),
[2](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHFZNmr7emMz5kNZgN_-1bDabBVDP-ZJaLWV1axXOdQIVFOkeg93okDZ1bTwndSs77Y3lLkGiprl7OgmmHYYrJR
[5](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFIBR279yUwTlwwyPncCRXbHqsQzM_65V1WxmFzAmtIQIS0jWzq_KOeVH1dbvjmbnaMPOBeQkzYNE-lvqsLyLeD-iOKYbzJ1u42MBXzKxW56Nn8iByp1aZWbsy90BQLjg==)5vGLdx8Ft1SE_bXNdREkWUzAkJGyo-HwIu3eD0Vyne91XWBYGNxyHaq8M74UUJpTZFiDxXT2SRujch5PQnrZaNn5Eg==),
[7](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIY
[6](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG-glb6ujV03_UbpmBkYLTHs8WuKtKoK3eNQ90RfBnE5mpEQsidzUiBpUuPD4PY5PXkqW1kp3j_ZgaW_VMiolKCtFRCvnyW2gXgPnRb6moBzJz_zdEe3CXqDvjd2czSqTW-wKJnBsz2DlJPnq2ubs-XcmRkel33jetOsbf4HNdNHJj_3Rc=)QHPo3iCZ3DGb0HyHg42xi-VCaNFXfoZzHbhNTw3NK8AmWBHDZrBxZ27fGPNddHrAgy9rxvFAGiESWrf8XmP91X3k12FcQyRmLQwNNVYdAYt9GETHkFIgs9SCVQ9hYQDNTl6BEeAkRs=),
[8](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEQUVTbaYZHi5F5PsY5pwTKs3a9DGieS95hxY9FBu4L3QdPzeAlSYung220zEw5VupcbPr0Y7MXJKfq4Ys-UQQDhZ4OGlWkldksgc2xeWAbQi9s1xypdQXZ3JR2Q8s1paMq),
[3](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHpWRHbkgVYf9qJnaGV0jcEnCKPH-xRrEZI1WC8hy44HYON4vtOXjOXPl6W1vlX2sjcxn9U7UWV6CPs6eZi75FbbqGtElIVi9uXPGhgzByw19Ueu2_cYe1uRBSf3OwwLj-KnKBu8PhpmNmcWNQzfG1qssxg0yX7xy335UmqfAvcaSUqgBTxiisPS4ADJyd-ckSHHYNH0yXr)    """

    # --- 修正点: この行を元に戻しました ---
    # 2. テキストからURLを抽出
    urls = extract_urls_from_text(input_text)

    # 3. メインの保存先フォルダを作成
    main_save_folder = "images_scraper"
    os.makedirs(main_save_folder, exist_ok=True)
    print(f"\nメインフォルダ '{main_save_folder}' の準備ができました。")
    print("-" * 50)

    # 4. 抽出した各URLを順番に処理
    if not urls:
        print("処理するURLが見つかりませんでした。")
    else:
        for i, url in enumerate(urls):
            # 5. 連番のサブフォルダを作成 (例: 01, 02, ...)
            sub_folder_name = str(i + 1).zfill(2)
            sub_folder_path = os.path.join(main_save_folder, sub_folder_name)
            os.makedirs(sub_folder_path, exist_ok=True)
            
            print(f"\n処理中: フォルダ '{sub_folder_name}' ({i+1}/{len(urls)})")

            # 6. 画像をダウンロード
            scrape_and_download_images(url, sub_folder_path)
            
            # 7. 元のURLを保存
            link_filepath = os.path.join(sub_folder_path, "source_link.txt")
            with open(link_filepath, 'w', encoding='utf-8') as f:
                f.write(url)
            print(f"    -> 元のURLを 'source_link.txt' に保存完了。")

    print("-" * 50)
    print("全てのタスクが完了しました。")
