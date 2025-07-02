import os
import shutil
from pathlib import Path

# 设置源文件夹（替换为你实际的桌面路径）
source_folder = Path(r"C:\Users\liu.huayun\Desktop\新しいフォルダー")

# 设置目标文件夹
target_folder = Path(r"C:\Users\liu.huayun\Desktop\all_images")

# 创建目标文件夹（如果不存在）
target_folder.mkdir(parents=True, exist_ok=True)

# 支持的图片格式
image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}

# 文件计数器（用于防止重名）
counter = 0

# 遍历所有子目录和文件
for root, dirs, files in os.walk(source_folder):
    for file in files:
        ext = Path(file).suffix.lower()
        if ext in image_extensions:
            counter += 1
            src_path = Path(root) / file

            # 防止目标文件夹中出现重名
            new_file_name = f"{Path(file).stem}_{counter}{ext}"
            dst_path = target_folder / new_file_name

            # 复制文件（如需移动，用 shutil.move）
            shutil.copy2(src_path, dst_path)
            print(f"复制: {src_path} → {dst_path}")

print("✅ 全部图片已复制完成！")
