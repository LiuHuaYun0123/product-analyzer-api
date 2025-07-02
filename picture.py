import os
from PIL import Image
import csv
import pillow_avif  # 注册 AVIF 插件
from pathlib import Path

# 获取桌面路径（支持 Windows 和 macOS/Linux）
from pathlib import Path
target_folder = Path(r"C:\Users\liu.huayun\Desktop\all_images")

# 支持的图片格式
image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

# CSV 输出文件名
output_csv ="image_data.csv"

# 收集图片数据
image_data = []

for root, dirs, files in os.walk(target_folder):
    for file in files:
        ext = Path(file).suffix.lower()
        if ext in image_extensions:
            full_path = os.path.join(root, file)
            try:
                with Image.open(full_path) as img:
                    width, height = img.size
                    item_id = Path(file).stem  # 文件名（不带扩展）
                    image_data.append({
                        "item_id": item_id,
                        "height": height,
                        "width": width,
                        "path": file  # 文件名加扩展名
                    })
            except Exception as e:
                print(f"无法读取图片 {file}: {e}")

# 写入 CSV 文件
with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["item_id", "height", "width", "path"])
    writer.writeheader()
    for row in image_data:
        writer.writerow(row)

print(f"完成！数据已保存为：{output_csv}")
