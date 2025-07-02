import pandas as pd
import json
import random

# --- 配置 ---
input_csv_path = r'data.csv'  # 输入 CSV 文件路径
output_jsonl_path = 'products_data_noname.jsonl'  # 输出 JSONL 文件路径
# --- 配置结束 ---

# 所有列名（CSV 实际无表头）
columns_to_extract = [
    "product_management_code", 
    "entry_category_name",  "category_code",
    "category_name", "major_classification_code", "major_classification_name", "medium_classification_code",
    "medium_classification_name", "manufacturer_code", "manufacturer_name", "manufacturer_name_kana",
    "manufacturer_official_name", "manufacturer_name_english", "brand_name", "model_number", "vendor_code",
    "vendor_name", "vendor_product_code", "common_name", "product_name", "origin_area_name", "material_1",
    "material_2", "material_3", "color_1", "color_2", "numeric_value_1", "unit_1_name", "numeric_value_2",
    "unit_2_name", "feature_1_design", "feature_2_usage_scene", "feature_3_waterproof", "product_note_1",
    "product_note_2", "season_name", "gender_code", "gender_name", "age_group_code", "age_group_name",
    "standard_code", "standard_name", "model_year", "weight", "weight_unit", "actual_size_1", "actual_size_2",
    "actual_size_3", "size_value", "size_unit", "size_specific_notes", "supplier_code", "supplier_name",
    "purchase_unit_price", "cost_price_excl_tax_new", "cost_price_incl_tax_new", "moving_average_cost",
    "selling_price_excl_tax_new", "selling_price_incl_tax_new", "reference_price_category_name", "msrp_incl_tax",
    "msrp_excl_tax", "msrp_update_date", "msrp_notes", "planned_sales_amount", "planned_sales_update_date",
    "planned_sales_notes", "market_price", "market_price_update_date", "market_price_notes", "base_buyback_price",
    "base_buyback_price_update_date", "base_buyback_price_notes", "individual_item_management_code",
    "individual_item_management_name", "cost_calculation_unit_code", "cost_calculation_unit_name", "sales_start_date",
    "sales_end_date", "manufacturer_warranty_period", "tax_exemption_category_code", "tax_exemption_category_name",
    "keyword_1", "keyword_2", "keyword_3", "keyword_4", "keyword_5", "keyword_6", "keyword_7", "keyword_8",
    "keyword_9", "keyword_10", "image_discontinued_date", "confirmation_status_code", "confirmation_status_name",
    "reservation_latest_deadline", "reservation_earliest_deadline", "standard_item_management_code",
    "standard_item_management_name", "md_management_setting_code", "md_management_setting_name", "max_stock_quantity",
    "stock_reorder_point", "new_item_first_purchase_date", "abolition_date", "created_at", "updated_at"
]

# 原始字段（去掉 keyword_1~10，准备加 keyword）
columns_needed = [
    "product_management_code", "entry_category_name", "category_name", "major_classification_name", "medium_classification_name",
    "manufacturer_name", "manufacturer_name_kana", "model_number",
    "common_name", "product_name", "material_1", "material_2", "color_1", "color_2",
    "feature_1_design", "feature_3_waterproof", "gender_name","actual_size_1", "actual_size_2",
    "actual_size_3","size_value"
]

# 读取 CSV，无表头
df = pd.read_csv(input_csv_path, encoding='utf-8', dtype=str, header=None)
df.columns = columns_to_extract
df = df.fillna("")  # NaN 转为空字符串

# --- 新功能 1：合并 keyword_1 ~ keyword_10 为 keyword 字段 ---
keyword_columns = [f"keyword_{i}" for i in range(1, 11)]
df["keyword"] = df[keyword_columns].apply(lambda row: " ".join(v for v in row if v.strip()), axis=1)

# 更新 columns_needed，移除 keyword_1~10，添加 keyword
columns_needed.append("keyword")

# --- 新功能 2：创建 priority_high，拼接指定字段值（不带字段名） ---
priority_fields = [
    "entry_category_name", "category_name", "major_classification_name", "manufacturer_name", 
    "product_name", "material_1", "material_2", "color_1", "color_2",
    "gender_name","actual_size_1", "actual_size_2",
    "actual_size_3","size_value"
]

def build_priority_high(row):
    seen_values = set()
    parts = []
    for col in priority_fields:
        value = row[col].strip()
        if value and value not in seen_values:
            parts.append(value)
            seen_values.add(value)
    return " ".join(parts)

df["priority_high"] = df.apply(build_priority_high, axis=1)
df["popularity"] = df.apply(lambda _: round(random.uniform(1, 100), 2), axis=1)

# 添加 priority_high 和 popularity 字段到最终输出字段中
columns_needed.append("priority_high")
columns_needed.append("popularity")

# 提取字段并写入 JSONL
df_filtered = df[columns_needed]

with open(output_jsonl_path, 'w', encoding='utf-8') as jsonl_file:
    for _, row in df_filtered.iterrows():
        row_dict = row.to_dict()
        json_line = json.dumps(row_dict, ensure_ascii=False)
        jsonl_file.write(json_line + '\n')

print(f"CSV 文件成功转换为 JSONL 文件：{output_jsonl_path}")
