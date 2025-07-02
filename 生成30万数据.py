import pandas as pd
import json
import os

input_file = 'expanded_300000.jsonl'
output_dir = 'expanded_parts'
os.makedirs(output_dir, exist_ok=True)

code_col = 'product_management_code'
num_parts = 50  # 要生成的文件数
base_filename = 'expanded_part_{:02d}.jsonl'

# === 读取已有的 30 万条数据
df = pd.read_json(input_file, lines=True, dtype=str)
original_len = len(df)

# === 提取已有编号，找到下一个编号起点
existing_codes = set(df[code_col])
numeric_codes = [int(code) for code in existing_codes if code.isdigit()]
next_code = max(numeric_codes) + 1 if numeric_codes else 1

print(f"原始数据共 {original_len} 条，将生成 {num_parts} 个文件，每个含 {original_len} 条，共 {original_len * num_parts:,} 条数据。")

def clean_json_string_fields(obj):
    for k, v in obj.items():
        if isinstance(v, str):
            v = v.replace('\n', ' ').replace('\r', ' ').replace('"', '”').replace('\\', '＼')
            obj[k] = v
    return obj

def safe_write_json_line(obj, file, line_num):
    try:
        obj = clean_json_string_fields(obj)
        json_str = json.dumps(obj, ensure_ascii=False)
        json.loads(json_str)  # 确保合法
        file.write(json_str + '\n')
    except Exception as e:
        print(f"❌ 第 {line_num} 行写入失败：{e}")

for part_num in range(1, num_parts + 1):
    output_file = os.path.join(output_dir, base_filename.format(part_num))
    print(f"📝 正在生成 {output_file} ...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for i in range(original_len):
            row = df.iloc[i].copy()

            while True:
                new_code = str(next_code).zfill(13)
                if new_code not in existing_codes:
                    break
                next_code += 1

            row[code_col] = new_code
            existing_codes.add(new_code)
            next_code += 1

            safe_write_json_line(row.to_dict(), f, (part_num - 1) * original_len + i + 1)

            if (i + 1) % 50000 == 0:
                f.flush()
                print(f"  ✅ 已写入 {i + 1:,} 条")

    print(f"✅ 文件 {output_file} 写入完成。")

print("🎉 所有文件生成完毕。")
