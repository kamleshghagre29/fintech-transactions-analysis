"""Fintech transactions analysis.

Steps: load -> clean -> KPIs -> trends -> charts -> summary
Run: python analysis.py   (run generate_data.py first)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

Path("images").mkdir(exist_ok=True)

# ---------- 1. Load ----------
df = pd.read_csv("transactions.csv", parse_dates=["timestamp"])
print("Raw shape:", df.shape)

# ---------- 2. Clean ----------
before = len(df)
df = df.drop_duplicates(subset="transaction_id")
print(f"Duplicates removed: {before - len(df)}")

df["city"] = df["city"].fillna("Unknown")
missing_amount = df["amount"].isna().sum()
df = df.dropna(subset=["amount"])  # a transaction without an amount is not usable
print(f"Rows with missing amount removed: {missing_amount}")

df["month"] = df["timestamp"].dt.to_period("M").astype(str)
df["hour"] = df["timestamp"].dt.hour
print("Clean shape:", df.shape)

# ---------- 3. KPIs (volume from successful transactions only) ----------
ok = df[df["status"] == "Success"]
kpis = {
    "Total transactions": len(df),
    "Successful transactions": len(ok),
    "Failure rate (%)": round((df["status"] == "Failed").mean() * 100, 2),
    "Total volume (Rs)": round(ok["amount"].sum(), 2),
    "Average ticket size (Rs)": round(ok["amount"].mean(), 2),
    "Unique customers": df["customer_id"].nunique(),
}
print("\n--- KPIs ---")
for k, v in kpis.items():
    print(f"{k}: {v:,}")

# ---------- 4. Analysis ----------
monthly = ok.groupby("month")["amount"].sum()
by_category = ok.groupby("category")["amount"].sum().sort_values(ascending=False)
fail_by_method = (
    df.assign(failed=df["status"] == "Failed")
    .groupby("payment_method")["failed"].mean().mul(100).round(2)
    .sort_values(ascending=False)
)
by_city = ok.groupby("city")["amount"].sum().sort_values(ascending=False)
top_customers = ok.groupby("customer_id")["amount"].sum().nlargest(10)

# Outliers (IQR method): flag very large transactions for review
q1, q3 = ok["amount"].quantile([0.25, 0.75])
upper = q3 + 1.5 * (q3 - q1)
outliers = ok[ok["amount"] > upper]
print(f"\nOutlier threshold: Rs {upper:,.0f} | Outlier transactions: {len(outliers)}")

# ---------- 5. Charts ----------
def save_bar(series, title, ylabel, fname, kind="bar", color="#2E86AB"):
    ax = series.plot(kind=kind, figsize=(8, 4.5), color=color)
    ax.set_title(title, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(f"images/{fname}", dpi=120)
    plt.close()

save_bar(monthly, "Monthly Transaction Volume", "Rs", "monthly_volume.png", kind="line")
save_bar(by_category, "Volume by Category", "Rs", "volume_by_category.png")
save_bar(fail_by_method, "Failure Rate by Payment Method", "% failed",
         "failure_by_method.png", color="#C0392B")

# ---------- 6. Summary file ----------
with open("summary.md", "w", encoding="utf-8") as f:
    f.write("# Analysis Summary\n\n## KPIs\n")
    for k, v in kpis.items():
        f.write(f"- {k}: {v:,}\n")
    f.write("\n## Insights\n")
    f.write(f"- Category with highest volume: **{by_category.index[0]}**\n")
    f.write(f"- Highest failure rate: **{fail_by_method.index[0]}** "
            f"({fail_by_method.iloc[0]}%)\n")
    f.write(f"- Top city by volume: **{by_city.index[0]}**\n")
    f.write(f"- Peak month: **{monthly.idxmax()}**\n")
    f.write(f"- Top 10 customers contribute "
            f"{top_customers.sum() / ok['amount'].sum() * 100:.1f}% of total volume\n")
print("\nsummary.md and images/ created")
