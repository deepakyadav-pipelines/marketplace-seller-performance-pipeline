
from pathlib import Path
import pandas as pd

SILVER = Path("data/silver")
INTERNAL = Path("data/internal")

products = pd.read_csv(SILVER / "olist_products.csv")
translations = pd.read_csv(SILVER / "product_category_translation.csv")
patches = pd.read_csv(INTERNAL / "category_translation_patch.csv")

# Normalize category keys and translation values
for df in [products, translations, patches]:
    df["product_category_name"] = (
        df["product_category_name"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

for df in [translations, patches]:
    df["product_category_name_english"] = (
        df["product_category_name_english"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

# Build translation lookup
kaggle_map = dict(zip(
    translations["product_category_name"],
    translations["product_category_name_english"]
))

patch_map = dict(zip(
    patches["product_category_name"],
    patches["product_category_name_english"]
))

def resolve_category(category):
    if pd.isna(category) or category == "":
        return "uncategorized", "missing_category"

    if category in patch_map:
        return patch_map[category], "manual_patch"

    if category in kaggle_map:
        return kaggle_map[category], "kaggle_translation"

    return "unknown", "translation_missing"


resolved = products["product_category_name"].apply(resolve_category)

products["category_name_english"] = resolved.apply(lambda x: x[0])
products["category_resolution_source"] = resolved.apply(lambda x: x[1])

# Save resolved products
output_file = SILVER / "olist_products_resolved.csv"
products.to_csv(output_file, index=False)

# Save audit report
audit = (
    products.groupby(
        ["category_resolution_source", "category_name_english"],
        dropna=False
    )
    .size()
    .reset_index(name="product_count")
)

audit.to_csv(
    SILVER / "category_resolution_audit.csv",
    index=False
)

print("Total products:", len(products))
print("\nResolution summary:")
print(products["category_resolution_source"].value_counts())

print("\nEnglish category summary:")
print(products["category_name_english"].value_counts().head(15))

print("\nOutput:", output_file)
print("Audit:", SILVER / "category_resolution_audit.csv")
