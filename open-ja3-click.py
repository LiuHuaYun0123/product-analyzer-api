import boto3
import json
import logging
import jaconv
import pandas as pd
import numpy as np
import os

def search_cloudformation_output(stackname, key):
    cloudformation_client = boto3.client("cloudformation", region_name=default_region)
    for output in cloudformation_client.describe_stacks(StackName=stackname)["Stacks"][0]["Outputs"]:
        if output["OutputKey"] == key:
            return output["OutputValue"]
    raise ValueError(f"{key} is not found in outputs of {stackname}.")

default_region = boto3.Session().region_name
logging.getLogger().setLevel(logging.ERROR)

def process_csv_to_dataframe(input_file_path):
    documents = []
    
    try:
        print(f"正在从 '{input_file_path}' 读取数据...")
        # 1. 手动以 UTF-8 读取文件并解析 JSON Lines
        with open(input_file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if line:  # 确保行不为空
                    try:
                        doc = json.loads(line)

                        # 合并后的优先级高字段
                        priority_high = ""

                        # 合并 `entry_category_name` 和 `category_name`
                        entry_category_value = doc.get("entry_category_name") if doc.get("entry_category_name") else "null"
                        priority_high += f"entry_category_name：{entry_category_value} "
                        
                        category_value = doc.get("category_name") if doc.get("category_name") else "null"
                        priority_high += f"category_name：{category_value} "

                        # 合并 `manufacturer_name` 和 `manufacturer_name_kana`
                        manufacturer_value = doc.get("manufacturer_name") if doc.get("manufacturer_name") else "null"
                        priority_high += f"manufacturer_name：{manufacturer_value} "
                        
                        manufacturer_kana_value = doc.get("manufacturer_name_kana") if doc.get("manufacturer_name_kana") else "null"
                        priority_high += f"manufacturer_name_kana：{manufacturer_kana_value} "

                        # 合并 `model_number`，如果为空则使用 "null"
                        model_value = doc.get("model_number") if doc.get("model_number") else "null"
                        priority_high += f"model_number：{model_value} "

                        # 合并 `common_name` 和 `product_name`
                        common_name_value = doc.get("common_name") if doc.get("common_name") else "null"
                        priority_high += f"common_name：{common_name_value} "
                        
                        product_name_value = doc.get("product_name") if doc.get("product_name") else "null"
                        priority_high += f"product_name：{product_name_value} "
                        
                        # 如果存在 `color_1` 字段，添加到 `priority_high`
                        color1_value = doc.get("color_1") if doc.get("color_1") else "null"
                        priority_high += f"color_1：{color1_value} "

                        # 如果存在 `color_2` 字段，添加到 `priority_high`
                        color2_value = doc.get("color_2") if doc.get("color_2") else "null"
                        priority_high += f"color_2：{color2_value} "

                        # 将合成的字段添加到文档中
                        doc["priority_high"] = priority_high.strip()

                        # 删除不需要的字段 `priority_low`，如果存在
                        if "priority_low" in doc:
                            del doc["priority_low"]

                        documents.append(doc)

                    except json.JSONDecodeError as json_err:
                        print(f"警告：跳过第 {i+1} 行，JSON 解析错误: {json_err}")
                        continue  # 跳过无法解析的行

        print(f"成功读取 {len(documents)} 个文档。")

        # 将处理后的文档转换为 DataFrame
        df = pd.DataFrame(documents)

        # 确保 priority_high 作为最后一列
        columns = [col for col in df.columns if col != "priority_high"] + ["priority_high"]
        df = df[columns]
        
        # 添加随机点击率和购买率（0 到 5 之间，保留 1 位小数）
        df["click_rate"] = np.round(np.random.uniform(0, 1, size=len(df)), 2)
        df["purchase_rate"] = np.round(np.random.uniform(0, 1, size=len(df)), 2)

        return df

    except FileNotFoundError:
        print(f"错误：文件未找到 '{input_file_path}'")
        return pd.DataFrame()  # 返回空 DataFrame
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        return pd.DataFrame()  # 返回空 DataFrame


def save_dataframe_to_jsonl(df, output_file_path):
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            for record in df.to_dict(orient="records"):
                json.dump(record, f, ensure_ascii=False)
                f.write("\n")
        print(f"成功保存为 JSONL 文件：{output_file_path}")
    except Exception as e:
        print(f"保存 JSONL 文件时发生错误: {e}")

# 调用函数并输出 DataFrame
processed_jsonl_file_path = "C:/Users/liu.huayun/Desktop/text/processed_products_v1.jsonl"
df = process_csv_to_dataframe(processed_jsonl_file_path)

# 打印 DataFrame 内容
print(df)

# 将处理后的 DataFrame 保存为 JSONL 文件
output_jsonl_file_path = "C:/Users/liu.huayun/Desktop/text/processed_output.jsonl"
save_dataframe_to_jsonl(df, output_jsonl_file_path)