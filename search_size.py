import logging
import re
import requests
from requests_aws4auth import AWS4Auth
import os

import boto3
import json
import logging
import jaconv
import awswrangler as wr
import pandas as pd
import numpy as np
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth


default_region = boto3.Session().region_name
logging.getLogger().setLevel(logging.ERROR)

cloudformation_stack_name = "searchdomain"
opensearch_cluster_endpoint = "search-mynewdomain-idwnyn6seif2n5pbqi4whraany.ap-northeast-1.es.amazonaws.com"

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

# 数字 + 单位的组合（比如 44cm, 45 mm, 10号 等）
NUMERIC_UNITS = ['cm', 'mm', '号', 'inch', 'インチ', 'サイズ']

# 字母型命名尺寸（通常出现在包包/品牌商品）
NAMED_SIZES = [
    'PM', 'MM', 'GM', 'MINI', 'MICRO', 'NANO', 'MAXI', 'PETITE', 'SMALL', 'MEDIUM', 'LARGE'
]

# S/M/L 尺码映射
SIZE_ALIASES = {
    'S': 'Sサイズ',
    'M': 'Mサイズ',
    'L': 'Lサイズ',
    'XL': 'XLサイズ',
    'XXL': 'XXLサイズ',
    'フリー': 'フリーサイズ'
}

def extract_size_from_query(query):
    sizes = []

    # 1. 匹配数字 + 单位（如 44cm, 45 mm, 10号）
    pattern_numeric = r'(\d{1,4})\s*(' + '|'.join(map(re.escape, NUMERIC_UNITS)) + r')'
    matches_numeric = re.findall(pattern_numeric, query, flags=re.IGNORECASE)
    for num, unit in matches_numeric:
        sizes.append((num + unit).upper())

    # 2. 匹配命名尺寸（如 PM, MM, MINI 等），注意大小写
    pattern_named = r'\b(' + '|'.join(NAMED_SIZES) + r')\b'
    matches_named = re.findall(pattern_named, query, flags=re.IGNORECASE)
    for size in matches_named:
        sizes.append(size.upper())

    # 3. 匹配 S/M/L 等服装常用码
    pattern_alias = r'\b(' + '|'.join(SIZE_ALIASES.keys()) + r')\b'
    matches_alias = re.findall(pattern_alias, query, flags=re.IGNORECASE)
    for alias in matches_alias:
        sizes.append(SIZE_ALIASES[alias.upper()])

    return sizes

def search_opensearch(query):
    # 提取尺寸信息
    sizes = extract_size_from_query(query)
    print("提取到的尺寸:", sizes)

    # 设定 OpenSearch URL 和索引名称
    OPENSEARCH_URL = "https://search-mynewdomain-idwnyn6seif2n5pbqi4whraany.ap-northeast-1.es.amazonaws.com"

    products_v1 = "products_v1"  # 替换为您的索引名称

    # 构建查询 URL
    url = f"{OPENSEARCH_URL}/{products_v1}/_search"

    headers = {
        'Content-Type': 'application/json',
    }
    body = {
        "query": {
            "match": {
                "product_name": query
            }
        }
    }

    # 发起请求
    response = requests.get(url, auth=auth, headers=headers, json=body)

    if response.status_code == 200:
        return response.json()  # 返回结果
    else:
        return {"error": response.text}  # 错误处理

# 示例调用
query = "PM バッグ"
result = search_opensearch(query)
print(result)
