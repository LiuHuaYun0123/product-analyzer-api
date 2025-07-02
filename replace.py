import pandas as pd

# 读取CSV文件
csv_file_path = 'merged_deduplicated_output.csv'
df = pd.read_csv(csv_file_path)

# 逐列检查并替换换行符
for column in df.columns:
    # 如果列是字符串类型，才进行替换
    if df[column].dtype == 'object':
        df[column] = df[column].str.replace('\n', ' ', regex=False)  # 替换换行符为一个空格
        df[column] = df[column].str.replace('\r', ' ', regex=False)  # 替换回车符为一个空格

# 将修改后的 DataFrame 写回到新的 CSV 文件
output_csv_file_path = 'modified_file.csv'
df.to_csv(output_csv_file_path, index=False, encoding='utf-8-sig')

print(f"处理完毕，替换后的 CSV 文件已保存为: {output_csv_file_path}")
