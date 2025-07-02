from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3

# === 配置 ===
region = boto3.Session().region_name
credentials = boto3.Session().get_credentials()
service = 'es'
host = 'search-productdomain-ejvjlr2d566odegkwlfp6he7iy.ap-northeast-1.es.amazonaws.com'  # ← 改成你的域名
index_name = 'products_v1'  # ← 改成你的索引名

# === 认证和连接 ===
auth = AWSV4SignerAuth(credentials, region, service)

client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

# === 统计文档总数 ===
response = client.count(index=index_name)
count = response['count']

print(f"索引 '{index_name}' 中共有文档数量: {count}")
