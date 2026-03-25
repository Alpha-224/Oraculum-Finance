import pandas as pd
import json
from datetime import datetime

# structure: transaction_id,date,description,amount,type,running_balance,source,category,is_duplicate

# 1. LOAD RAW CSV
df=pd.read_csv("deepseek_csv_20260325_9c591b.txt")
print("=== BEFORE CLEANING ===")
print(df.head())
print(f"\nDate formats: {df['date'].unique()}")

# 2. CLEAN DATES
# Convert all dates to YYYY-MM-DD
df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

# 3. CLEAN AMOUNTS
# Ensure all amounts are float, handle negatives
df['amount'] = df['amount'].astype(float)

# 4. FIX INCONSISTENT DATA
# Ensure expenses are negative
df.loc[(df['type'] == 'expense') & (df['amount'] > 0), 'amount'] = -df['amount']

# 5. REMOVE DUPLICATES
# Check for duplicates based on transaction_id
df = df.drop_duplicates(subset=['transaction_id'])

# 6. HANDLE MISSING VALUES
# Fill missing categories with 'uncategorized'
df['category'] = df['category'].fillna('uncategorized')

print("\n=== AFTER CLEANING ===")
print(df.head())
print(f"\nDate formats: {df['date'].unique()}")

# 7. CONVERT TO JSON
# Option A: One JSON object with all records
json_output = df.to_json(orient='records', indent=2)

# Option B: Save to file
with open('transactions_cleaned.json', 'w') as f:
    f.write(json_output)

print("\n✅ Cleaned JSON saved to transactions_cleaned.json")