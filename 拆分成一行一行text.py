import os
import json

# 输入文件路径
input_file = "processed_products_v1.jsonl"

# 输出文件夹路径
output_dir = "output_texts"
os.makedirs(output_dir, exist_ok=True)

# 逐行读取并保存为 .txt 文件
with open(input_file, "r", encoding="utf-8") as infile:
    for i, line in enumerate(infile, start=1):
        # 可选：解析 JSON 内容（只保存某字段）
        try:
            data = json.loads(line)
            content = str(data)  # 你可以改为 data['text'] 等
        except json.JSONDecodeError:
            content = line.strip()  # 如果不是标准 JSON，就原样输出

        # 写入 .txt 文件
        filename = os.path.join(output_dir, f"{i:06}.txt")
        with open(filename, "w", encoding="utf-8") as outfile:
            outfile.write(content)
