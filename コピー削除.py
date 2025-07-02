import os
from pathlib import Path

# 设置目标文件夹路径（替换为你的桌面文件夹路径）
target_folder = Path(r"C:\Users\liu.huayun\Desktop\all_images")

# 支持的图片扩展名
image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

# 计数器
deleted_files = 0

# 遍历文件夹中的所有文件
for file in target_folder.iterdir():
    if file.is_file():
        if file.suffix.lower() in image_extensions and "コピー" in file.stem:
            try:
                file.unlink()  # 删除文件
                print(f"已删除: {file.name}")
                deleted_files += 1
            except Exception as e:
                print(f"无法删除 {file.name}: {e}")

print(f"\n操作完成，总共删除了 {deleted_files} 个文件。")
