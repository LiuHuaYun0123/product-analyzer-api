import os
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------------------------------------------------------------
# 函数: 从指定URL抓取并下载图片 (已根据您的新要求修改)
# -----------------------------------------------------------------------------
def scrape_and_download_images(url: str, save_folder: str, num_images_to_download: int = 5) -> list:
    """
    使用Selenium访问URL，解析页面，并只下载JPG/JPEG格式的图片。
    """
    if not url: return []
    print(f"\n--- 正在处理链接: {url} ---")
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
        if not os.path.exists(save_folder): os.makedirs(save_folder)
        all_imgs = soup.find_all('img')
        downloaded_images = []
        for img_tag in all_imgs:
            if len(downloaded_images) >= num_images_to_download: break
            img_url = img_tag.get('src')
            if not img_url or 'base64' in img_url or 'svg' in img_url: continue
            
            img_url = urljoin(url, img_url)

            # --- 修改点: 仅保留JPG/JPEG图片 ---
            # 检查链接（去除URL参数后）是否以 .jpg 或 .jpeg 结尾（不区分大小写）
            path = urlparse(img_url).path
            if not (path.lower().endswith('.jpg') or path.lower().endswith('.jpeg')):
                continue # 如果不是JPG或JPEG格式，则跳过此图片，继续处理下一个

            try:
                img_response = requests.get(img_url, stream=True, timeout=10)
                if img_response.status_code == 200:
                    filename_base = os.path.basename(path) # 使用path部分作为文件名基础
                    safe_filename = "".join([c for c in filename_base if c.isalpha() or c.isdigit() or c in ('.', '_')]).rstrip()
                    if not safe_filename: safe_filename = f"image_{len(downloaded_images)+1}.jpg"
                    filepath = os.path.join(save_folder, safe_filename)
                    with open(filepath, 'wb') as f: f.write(img_response.content)
                    print(f"  -> 已下载 (JPG): {filepath}")
                    downloaded_images.append(filepath)
            except Exception: continue
        return downloaded_images
    finally:
        driver.quit()

# =============================================================================
# 主程序入口 (这部分代码完全没有改动)
# =============================================================================
if __name__ == "__main__":
    
    # --- 直接在这里输入您想抓取的链接 ---
    target_url = "https://houbidou.com/products/240500407749?_pos=41&_sid=2ab709728&_ss=r"
    # 您可以把上面的链接换成任何您想抓取的商品页面地址

    if target_url:
        # --- 根据URL生成一个简单的文件夹名 ---
        try:
            domain_name = urlparse(target_url).netloc.replace('www.', '').split('.')[0]
            save_directory = f"scraped_images_from_{domain_name}"
        except:
            save_directory = "scraped_images" # 如果URL格式有问题，则使用默认名

        print(f"--- 开始抓取任务 (仅限JPG/JPEG) ---")
        
        downloaded_files = scrape_and_download_images(
            url=target_url, 
            save_folder=save_directory,
            num_images_to_download=10 # 您可以调整想下载的图片数量
        )

        if downloaded_files:
            print("\n--- 任务完成 ---")
            print(f"源链接: {target_url}")
            print(f"共下载了 {len(downloaded_files)} 张JPG/JPEG图片，保存在文件夹: '{save_directory}'")
            for file in downloaded_files:
                print(f" - {file}")
        else:
            print(f"\n--- 任务完成 ---")
            print(f"在链接 {target_url} 上未能成功下载任何JPG/JPEG格式的图片。")
            print(f"请检查链接是否正确，或页面上没有符合条件的图片。")
    else:
        print("\n--- 任务开始失败 ---")
        print("请在 'target_url' 变量中提供一个有效的链接。")
