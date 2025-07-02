import boto3
import json
import logging
import jaconv
import awswrangler as wr
import pandas as pd
import numpy as np
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import os

from ipywidgets import interact

def search_cloudformation_output(stackname, key):
    cloudformation_client = boto3.client("cloudformation", region_name=default_region)
    for output in cloudformation_client.describe_stacks(StackName=stackname)["Stacks"][0]["Outputs"]:
        if output["OutputKey"] == key:
            return output["OutputValue"]
    raise ValueError(f"{key} is not found in outputs of {stackname}.")

default_region = boto3.Session().region_name
logging.getLogger().setLevel(logging.ERROR)

cloudformation_stack_name = "searchdomain"
opensearch_cluster_endpoint = "search-productdomain-ejvjlr2d566odegkwlfp6he7iy.ap-northeast-1.es.amazonaws.com"

credentials = boto3.Session().get_credentials()
service_code = "es"
auth = AWSV4SignerAuth(credentials=credentials, region=default_region, service=service_code)
opensearch_client = OpenSearch(
    hosts=[{"host": opensearch_cluster_endpoint, "port": 443}],
    http_compress=True, 
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class = RequestsHttpConnection
)

index_name = "products_v1"
#file_path = f"C:/Users/liu.huayun/Desktop/text/products_data.jsonl"
file_path = f"C:/Users/liu.huayun/Desktop/text/expanded_300000.jsonl"

# 新增：存放含空格的字段值
suspicious_values = set()

try:
    # 1. 手动以 UTF-8 读取文件并解析 JSON Lines
    documents = []
    print(f"正在从 '{file_path}' 读取数据...")
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line:
                try:
                    doc = json.loads(line)

                    # 清理字段中的多余双引号、换行符
                    for field in [ "product_management_code", "entry_category_name", "category_code", "category_name", "manufacturer_name", "manufacturer_name_kana",
                                  "manufacturer_official_name", "manufacturer_name_english", "brand_name", "model_number", "common_name", "product_name", "material_1", "gender_name"]:
                        if field in doc and isinstance(doc[field], str):
                            original_value = doc[field]
                            original_value = original_value.replace('\n', '').replace('\r', '').replace('"', '')
                            if " " in original_value:
                                suspicious_values.add(original_value)
                            normalized = jaconv.hira2kata(jaconv.z2h(jaconv.h2z(original_value), kana=False, digit=True, ascii=True))
                            normalized = normalized.replace(" ", "")
                            doc[field] = normalized

                    documents.append(doc)

                except json.JSONDecodeError as json_err:
                    print(f"警告：跳过第 {i+1} 行，JSON 解析错误: {json_err}")
                    continue

    print(f"成功读取 {len(documents)} 个文档。")

    # 处理并写入含空格字段到 CSV
    if suspicious_values:
        suspicious_csv_path = "C:/Users/liu.huayun/Desktop/text/suspicious_fields.csv"
        
        # 读取现有的 CSV 文件内容
        existing_values = set()
        if os.path.exists(suspicious_csv_path):
            with open(suspicious_csv_path, 'r', encoding='utf-8-sig') as f:
                existing_values = set(line.strip() for line in f if line.strip())

        # 筛选出不重复的字段值
        new_values = suspicious_values - existing_values

        if new_values:
            # ✅ 直接逐行写入，不使用 DataFrame，不写入列名
            with open(suspicious_csv_path, mode='a', encoding='utf-8-sig') as f:
                for value in new_values:
                    f.write(f"{value}\n")
            print(f"数据已追加到现有文件：{suspicious_csv_path}")
        else:
            print("没有新数据需要写入。")
    else:
        print("未发现包含空格的字段值。")

    # 2. 使用 index_documents 索引内存中的文档列表
    if documents:
        print(f"正在向索引 '{index_name}' 写入文档...")
        response = wr.opensearch.index_documents(
            client=opensearch_client,
            documents=documents,
            use_threads=True,
            index=index_name,
            bulk_size=200,
            refresh=False
        )
        print("数据索引成功！")
    else:
        print("文件中没有找到有效的文档，未执行索引操作。")

except FileNotFoundError:
    print(f"错误：文件未找到 '{file_path}'")
except Exception as e:
    print(f"处理过程中发生错误: {e}")
