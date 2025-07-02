import os
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------------------------------------------------------------
# 関数: 指定されたURLから「主要な」テキストのみを抽出し、ファイルに保存する (改良版)
# -----------------------------------------------------------------------------
def scrape_and_save_text(url: str, save_filepath: str):
    """
    Seleniumを使ってURLにアクセスし、ページの「主要な商品情報エリア」から
    テキストを抽出して.txtファイルに保存する。
    """
    if not url:
        print("URLが提供されていません。")
        return

    print(f"\n--- テキスト抽出を開始します: {url} ---")
    
    # Seleniumのセットアップ
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

        # --- ここからがテキスト抽出のロジック (改良版) ---

        # 1. 特定の「箱」を探す。これはウェブサイト毎に調整が必要です。
        #    Yahoo!ショッピングの場合、商品情報は 'id="ItemInfo"' のdivに格納されていることが多い。
        product_info_area = soup.find('div', id='ItemInfo')

        target_soup = None
        if product_info_area:
            print("  -> 主要な商品情報エリア ('#ItemInfo') を発見。このエリアからテキストを抽出します。")
            target_soup = product_info_area
        else:
            # もし指定の「箱」が見つからなかった場合（他のサイトの場合など）
            print("  -> 警告: 専用の商品情報エリアが見つかりませんでした。")
            print("  -> ページ中央の主要コンテンツと思われるエリアから抽出を試みます。")
            target_soup = soup.find('main') # HTML5の<main>タグを探す
            if not target_soup:
                target_soup = soup.body # それも見つからなければ、最終手段としてbody全体

        # 2. ターゲットエリア内の不要な要素（ヘッダー、フッター、ナビゲーション等）を削除
        for unwanted_tag in target_soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
            unwanted_tag.decompose()

        # 3. テキストを取得し、整形する
        text = target_soup.get_text(separator="\n", strip=True)
        
        # 連続する空行を削除して、よりクリーンなテキストにする
        cleaned_text = "\n".join(line for line in text.splitlines() if line.strip())
        
        # 4. テキストをファイルに保存
        with open(save_filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
            
        print(f"  -> テキストの抽出が完了し、'{save_filepath}' に保存しました。")
        return True

    except Exception as e:
        print(f"テキスト抽出中にエラーが発生しました: {e}")
        return False
    finally:
        driver.quit()

# =============================================================================
# 主プログラム (変更なし)
# =============================================================================
if __name__ == "__main__":
    
    # 直接ここに、テキストを抽出したいページのURLを入力してください
    target_url = "https://store.shopping.yahoo.co.jp/dsdaikokuya/dh59803.html"

    if target_url:
        try:
            domain_name = urlparse(target_url).netloc.replace('www.', '').split('.')[0]
            save_filepath = f"scraped_text_from_{domain_name}.txt"
        except:
            save_filepath = "scraped_text.txt"

        print(f"--- テキスト抓取タスクを開始 ---")
        
        success = scrape_and_save_text(
            url=target_url, 
            save_filepath=save_filepath
        )

        if success:
            print(f"\n--- タスク完了 ---")
            print(f"抽出元URL: {target_url}")
            print(f"保存ファイル: {save_filepath}")
        else:
            print(f"\n--- タスク失敗 ---")
            print(f"URL: {target_url} からテキストを抽出できませんでした。")
    else:
        print("\n--- タスク開始失敗 ---")
        print("'target_url' 変数に有効なURLを入力してください。")

