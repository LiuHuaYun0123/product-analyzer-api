import pandas as pd
import json
import numpy as np  # 确保导入 numpy

def squad_json_to_dataframe(input_file_path, record_path=["data", "paragraphs", "qas", "answers"]):
    # 使用 'utf-8-sig' 来处理 BOM 或编码问题
    with open(input_file_path, encoding='utf-8-sig') as f:
        file = json.loads(f.read())
    
    # 对不同的 record_path 进行 json_normalize
    m = pd.json_normalize(file, record_path[:-1])
    r = pd.json_normalize(file, record_path[:-2])

    # 创建索引，将 context 重复填充到 m DataFrame 中
    idx = np.repeat(r["context"].values, r.qas.str.len())
    m["context"] = idx

    # 对 'answers' 字段进行处理，确保是唯一的文本
    m["answers"] = m["answers"].apply(lambda x: np.unique(pd.json_normalize(x)["text"].to_list()))
    
    # 只保留需要的列
    return m[["id", "question", "context", "answers"]]

# 文件路径
valid_filename = "valid-v1.3.json"

# 调用函数
valid_df = squad_json_to_dataframe(valid_filename)

# 输出结果（如果需要）
print(valid_df.head())
