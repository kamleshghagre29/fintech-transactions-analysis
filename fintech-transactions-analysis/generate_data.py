"""Generates a synthetic fintech transactions dataset.

Some messiness (missing values, duplicates) is added on purpose,
like real-world data, so the cleaning step can be practiced.
Run: python generate_data.py
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 5000

customer_ids = [f"C{str(i).zfill(4)}" for i in range(1, 801)]
categories = ["Groceries", "Bills", "Shopping", "Travel", "Food", "Entertainment", "Transfers"]
methods = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"]
cities = ["Mumbai", "Delhi", "Bengaluru", "Pune", "Nagpur", "Hyderabad", "Chennai"]

dates = pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, N), unit="D")
dates = dates + pd.to_timedelta(rng.integers(0, 86400, N), unit="s")

method = rng.choice(methods, N, p=[0.45, 0.2, 0.15, 0.1, 0.1])
category = rng.choice(categories, N, p=[0.2, 0.15, 0.2, 0.1, 0.15, 0.1, 0.1])

# amount: lognormal, scaled slightly by category
scale = pd.Series(category).map({
    "Groceries": 1.0, "Bills": 1.4, "Shopping": 1.6, "Travel": 2.4,
    "Food": 0.7, "Entertainment": 0.9, "Transfers": 1.8,
}).values
amount = np.round(np.exp(rng.normal(6.0, 0.9, N)) * scale / 2, 2)

# status: failure probability differs by payment method
fail_p = pd.Series(method).map({
    "UPI": 0.03, "Credit Card": 0.05, "Debit Card": 0.05,
    "Net Banking": 0.09, "Wallet": 0.07,
}).values
status = np.where(rng.random(N) < fail_p, "Failed", "Success")

df = pd.DataFrame({
    "transaction_id": [f"T{str(i).zfill(6)}" for i in range(1, N + 1)],
    "customer_id": rng.choice(customer_ids, N),
    "timestamp": dates,
    "amount": amount,
    "category": category,
    "payment_method": method,
    "city": rng.choice(cities, N),
    "status": status,
}).sort_values("timestamp").reset_index(drop=True)

# Add messiness: missing values and duplicates
df.loc[rng.choice(N, 60, replace=False), "city"] = np.nan
df.loc[rng.choice(N, 25, replace=False), "amount"] = np.nan
df = pd.concat([df, df.sample(40, random_state=1)], ignore_index=True)

df.to_csv("transactions.csv", index=False)
print(f"transactions.csv created: {len(df)} rows")
