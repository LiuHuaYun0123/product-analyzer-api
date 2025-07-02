import io
from google.cloud import vision

def find_product_pages_with_vision(image_path: str, top_n: int = 5) -> list:
    """
    Google Vision APIのWeb Detection機能を最大限に活用し、
    画像に最も関連性の高い商品ページのURLをインテリジェントに検索・ソートして返す。

    Args:
        image_path (str): 分析するローカル画像のパス。
        top_n (int): 返す上位URLの数。

    Returns:
        list: スコアリングされてソートされた結果の辞書のリスト。
              例: [{'url': '...', 'title': '...', 'score': 5}]
    """
    print(f"\n--- Vision APIを使用して画像 '{image_path}' のWeb検索を開始します ---")
    
    try:
        client = vision.ImageAnnotatorClient()

        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)

        response = client.web_detection(image=image)
        annotations = response.web_detection

        # --- ステップ1: Vision APIから重要なコンテキスト情報を抽出 ---
        # Vision APIが最も可能性が高いと判断した画像の推測ラベル
        best_guesses = [label.label.lower() for label in annotations.best_guess_labels]
        # 画像に関連するWeb上のエンティティ（ブランド名、商品名など）
        web_entities = [entity.description.lower() for entity in annotations.web_entities if entity.score > 0.5]

        print("\n[Vision APIによる分析結果]")
        print(f"  - 最良推測ラベル: {best_guesses}")
        print(f"  - 主要なWebエンティティ: {web_entities}")

        # --- ステップ2: スコアリングのためのキーワード設定 ---
        # これらの単語がURLやタイトルに含まれていればスコアが加算される
        POSITIVE_KEYWORDS = {
            'product': 3, 'item': 3, 'detail': 2, 'goods': 2, 'shop': 1, 'store': 1,
            'rakuten.co.jp': 2, 'amazon.co.jp': 2, 'yahoo.co.jp': 2, 'zozo.jp': 2,
            'buy': 2, 'cart': 1
        }
        # これらのドメインは商品ページである可能性が低いため除外する
        NEGATIVE_DOMAINS = [
            'pinterest.com', 'instagram.com', 'facebook.com', 'twitter.com', 'x.com',
            'youtube.com', 'wikipedia.org', 'weibo.com', 'blog', 'news', 'forum'
        ]

        # --- ステップ3: 各ページを評価し、フィルタリングする ---
        scored_pages = []
        if not annotations.pages_with_matching_images:
            print("⚠️ この画像に一致するページは見つかりませんでした。")
            return []

        print(f"\n{len(annotations.pages_with_matching_images)} 件の一致ページを評価中...")
        for page in annotations.pages_with_matching_images:
            url = page.url.lower()
            title = (page.page_title or "").lower()
            score = 0

            # ネガティブドメインに含まれていれば即座に除外
            if any(domain in url for domain in NEGATIVE_DOMAINS):
                continue

            # ポジティブキーワードによる加点
            for keyword, weight in POSITIVE_KEYWORDS.items():
                if keyword in url or keyword in title:
                    score += weight
            
            # Webエンティティ（最重要）による加点
            for entity in web_entities:
                if entity in title or entity in url:
                    score += 5 # エンティティが一致した場合、大幅に加点

            # 最良推測ラベルによる加点
            for guess in best_guesses:
                if guess in title:
                    score += 2

            # スコアが0より大きいページのみを候補とする
            if score > 0:
                scored_pages.append({'url': page.url, 'title': page.page_title, 'score': score})

        if not scored_pages:
            print("⚠️ フィルタリング後、候補となる商品ページは見つかりませんでした。")
            return []
            
        # --- ステップ4: スコアの高い順にソートして返す ---
        sorted_results = sorted(scored_pages, key=lambda x: x['score'], reverse=True)
        
        print("\n--- 検索結果 (関連性の高い順) ---")
        for result in sorted_results[:top_n]:
            print(f"[スコア: {result['score']}] {result['title']}\n  -> {result['url']}")

        return sorted_results[:top_n]

    except Exception as e:
        print(f"❌ Vision APIの処理中にエラーが発生しました: {e}")
        return []


# =============================================================================
# 使用例
# =============================================================================
if __name__ == '__main__':
    # ここに検索したい画像のパスを指定してください
    # 例: query_image_path = "gucci_bag.jpg"
    query_image_path = "06.jpg" 
    
    # 新しい高精度な関数を呼び出す
    web_results = find_product_pages_with_vision(query_image_path, top_n=5)
    
    # この`web_results`をあなたのスクレイピング関数の入力として使用できます
    if web_results:
        print("\n--- 次のステップ ---")
        print("これらのURLをスクレイピング関数に渡して、画像やテキストをダウンロードできます。")
        # 例:
        # first_url = web_results[0]['url']
        # scrape_and_download_images(first_url, "scraped_folder")

