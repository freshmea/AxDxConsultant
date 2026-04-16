from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "retail_sales_dataset.xlsx"
OUTPUT_DIR = ROOT / "retail_sales_report_assets"


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customers = pd.read_excel(DATA_PATH, sheet_name="Customers")
    products = pd.read_excel(DATA_PATH, sheet_name="Products")
    stores = pd.read_excel(DATA_PATH, sheet_name="Stores")
    transactions = pd.read_excel(DATA_PATH, sheet_name="Transactions")

    customers["BirthDate"] = pd.to_datetime(customers["BirthDate"])
    customers["JoinDate"] = pd.to_datetime(customers["JoinDate"])
    transactions["Date"] = pd.to_datetime(transactions["Date"])

    customers["Age"] = ((pd.Timestamp("2026-04-16") - customers["BirthDate"]).dt.days / 365.25).round(1)
    customers["TenureDays"] = (pd.Timestamp("2026-04-16") - customers["JoinDate"]).dt.days

    sales = (
        transactions.merge(
            products[["ProductID", "ProductName", "Category", "SubCategory", "UnitPrice", "CostPrice"]],
            on="ProductID",
            how="left",
        )
        .merge(
            stores[["StoreID", "StoreName", "City", "Region"]].rename(columns={"City": "StoreCity"}),
            on="StoreID",
            how="left",
        )
        .merge(
            customers[["CustomerID", "Gender", "Age", "TenureDays"]], on="CustomerID", how="left"
        )
    )

    sales["GrossSales"] = sales["UnitPrice"] * sales["Quantity"]
    sales["NetSales"] = sales["GrossSales"] * (1 - sales["Discount"])
    sales["EstimatedCost"] = sales["CostPrice"] * sales["Quantity"]
    sales["EstimatedProfit"] = sales["NetSales"] - sales["EstimatedCost"]
    sales["ProfitMargin"] = sales["EstimatedProfit"] / sales["NetSales"]
    sales["YearMonth"] = sales["Date"].dt.to_period("M").astype(str)
    sales["Weekday"] = pd.Categorical(
        sales["Date"].dt.day_name(),
        categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        ordered=True,
    )

    return customers, products, stores, sales


def setup_style() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["figure.dpi"] = 140
    plt.rcParams["savefig.dpi"] = 160
    plt.rcParams["axes.unicode_minus"] = False


def save_plot(filename: str) -> None:
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, bbox_inches="tight")
    plt.close()


def plot_monthly_sales(sales: pd.DataFrame) -> None:
    monthly = sales.groupby("YearMonth", as_index=False)["NetSales"].sum()
    plt.figure(figsize=(14, 6))
    ax = sns.lineplot(data=monthly, x="YearMonth", y="NetSales", marker="o", linewidth=2.5, color="#1f77b4")
    ax.set_title("Monthly Net Sales Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Net Sales")
    ax.tick_params(axis="x", rotation=45)
    save_plot("01_monthly_net_sales_trend.png")


def plot_category_sales(sales: pd.DataFrame) -> None:
    category = sales.groupby("Category", as_index=False)["NetSales"].sum().sort_values("NetSales", ascending=False)
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=category, x="Category", y="NetSales", hue="Category", dodge=False, palette="Set2", legend=False)
    ax.set_title("Net Sales by Category")
    ax.set_xlabel("Category")
    ax.set_ylabel("Net Sales")
    save_plot("02_category_net_sales_bar.png")


def plot_subcategory_sales(sales: pd.DataFrame) -> None:
    subcategory = (
        sales.groupby("SubCategory", as_index=False)["NetSales"]
        .sum()
        .sort_values("NetSales", ascending=False)
        .head(10)
    )
    plt.figure(figsize=(12, 7))
    ax = sns.barplot(data=subcategory, y="SubCategory", x="NetSales", hue="SubCategory", dodge=False, palette="crest", legend=False)
    ax.set_title("Top 10 Subcategories by Net Sales")
    ax.set_xlabel("Net Sales")
    ax.set_ylabel("SubCategory")
    save_plot("03_top10_subcategory_net_sales_barh.png")


def plot_store_sales(sales: pd.DataFrame) -> None:
    stores = sales.groupby("StoreName", as_index=False)["NetSales"].sum().sort_values("NetSales", ascending=False)
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(data=stores, y="StoreName", x="NetSales", hue="StoreName", dodge=False, palette="flare", legend=False)
    ax.set_title("Net Sales by Store")
    ax.set_xlabel("Net Sales")
    ax.set_ylabel("Store")
    save_plot("04_store_net_sales_barh.png")


def plot_payment_methods(sales: pd.DataFrame) -> None:
    payment = sales["PaymentMethod"].value_counts().rename_axis("PaymentMethod").reset_index(name="Count")
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=payment, x="PaymentMethod", y="Count", hue="PaymentMethod", dodge=False, palette="pastel", legend=False)
    ax.set_title("Transaction Count by Payment Method")
    ax.set_xlabel("Payment Method")
    ax.set_ylabel("Transaction Count")
    save_plot("05_payment_method_counts_bar.png")


def plot_weekday_sales(sales: pd.DataFrame) -> None:
    weekday = sales.groupby("Weekday", as_index=False)["NetSales"].sum()
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(data=weekday, x="Weekday", y="NetSales", hue="Weekday", dodge=False, palette="Blues_d", legend=False)
    ax.set_title("Net Sales by Weekday")
    ax.set_xlabel("Weekday")
    ax.set_ylabel("Net Sales")
    ax.tick_params(axis="x", rotation=30)
    save_plot("06_weekday_net_sales_bar.png")


def plot_customer_age(customers: pd.DataFrame) -> None:
    plt.figure(figsize=(11, 6))
    ax = sns.histplot(data=customers, x="Age", bins=16, kde=True, color="#2a9d8f")
    ax.set_title("Customer Age Distribution")
    ax.set_xlabel("Age")
    ax.set_ylabel("Count")
    save_plot("07_customer_age_distribution_hist.png")


def plot_order_value_distribution(sales: pd.DataFrame) -> None:
    plt.figure(figsize=(11, 6))
    ax = sns.histplot(data=sales, x="NetSales", bins=30, kde=True, color="#e76f51")
    ax.set_title("Order Value Distribution")
    ax.set_xlabel("Net Sales per Transaction")
    ax.set_ylabel("Count")
    save_plot("08_order_value_distribution_hist.png")


def plot_discount_distribution(sales: pd.DataFrame) -> None:
    plt.figure(figsize=(10, 6))
    ax = sns.countplot(data=sales, x="Discount", hue="Discount", palette="mako", legend=False)
    ax.set_title("Discount Rate Distribution")
    ax.set_xlabel("Discount")
    ax.set_ylabel("Transaction Count")
    save_plot("09_discount_distribution_count.png")


def plot_quantity_distribution(sales: pd.DataFrame) -> None:
    plt.figure(figsize=(10, 6))
    ax = sns.countplot(data=sales, x="Quantity", hue="Quantity", palette="rocket", legend=False)
    ax.set_title("Quantity Distribution per Transaction")
    ax.set_xlabel("Quantity")
    ax.set_ylabel("Transaction Count")
    save_plot("10_quantity_distribution_count.png")


def plot_gender_sales(sales: pd.DataFrame) -> None:
    gender_sales = sales.groupby("Gender", as_index=False)["NetSales"].sum().sort_values("NetSales", ascending=False)
    plt.figure(figsize=(8, 6))
    ax = sns.barplot(data=gender_sales, x="Gender", y="NetSales", hue="Gender", dodge=False, palette="Set1", legend=False)
    ax.set_title("Net Sales by Gender")
    ax.set_xlabel("Gender")
    ax.set_ylabel("Net Sales")
    save_plot("11_gender_net_sales_bar.png")


def plot_category_sales_pie(sales: pd.DataFrame) -> None:
    category = sales.groupby("Category")["NetSales"].sum().sort_values(ascending=False)
    colors = sns.color_palette("Set2", n_colors=len(category))
    plt.figure(figsize=(8, 8))
    plt.pie(
        category.values,
        labels=category.index,
        autopct="%1.1f%%",
        startangle=90,
        counterclock=False,
        colors=colors,
        wedgeprops={"edgecolor": "white", "linewidth": 1.2},
    )
    plt.title("Category Share of Net Sales")
    save_plot("12_category_net_sales_pie.png")


def plot_payment_methods_pie(sales: pd.DataFrame) -> None:
    payment = sales["PaymentMethod"].value_counts().sort_values(ascending=False)
    colors = sns.color_palette("pastel", n_colors=len(payment))
    plt.figure(figsize=(8, 8))
    plt.pie(
        payment.values,
        labels=payment.index,
        autopct="%1.1f%%",
        startangle=90,
        counterclock=False,
        colors=colors,
        wedgeprops={"edgecolor": "white", "linewidth": 1.2},
    )
    plt.title("Payment Method Share")
    save_plot("13_payment_method_share_pie.png")


def plot_category_margin(sales: pd.DataFrame) -> None:
    category_margin = (
        sales.groupby("Category", as_index=False)[["NetSales", "EstimatedProfit"]]
        .sum()
        .assign(ProfitMargin=lambda df: df["EstimatedProfit"] / df["NetSales"])
        .sort_values("ProfitMargin", ascending=False)
    )
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=category_margin, x="Category", y="ProfitMargin", hue="Category", dodge=False, palette="viridis", legend=False)
    ax.set_title("Estimated Profit Margin by Category")
    ax.set_xlabel("Category")
    ax.set_ylabel("Profit Margin")
    save_plot("14_category_profit_margin_bar.png")


def write_manifest() -> None:
    manifest = """# Retail Sales Seaborn Graphs

- 01_monthly_net_sales_trend.png: 월별 순매출 추세
- 02_category_net_sales_bar.png: 카테고리별 순매출 비교
- 03_top10_subcategory_net_sales_barh.png: 상위 10개 서브카테고리 순매출
- 04_store_net_sales_barh.png: 매장별 순매출
- 05_payment_method_counts_bar.png: 결제수단별 거래 건수
- 06_weekday_net_sales_bar.png: 요일별 순매출
- 07_customer_age_distribution_hist.png: 고객 연령 분포
- 08_order_value_distribution_hist.png: 거래당 순매출 분포
- 09_discount_distribution_count.png: 할인율 분포
- 10_quantity_distribution_count.png: 거래 수량 분포
- 11_gender_net_sales_bar.png: 성별 순매출
- 12_category_net_sales_pie.png: 카테고리 순매출 비중 원그래프
- 13_payment_method_share_pie.png: 결제수단 비중 원그래프
- 14_category_profit_margin_bar.png: 카테고리별 추정 이익률
"""
    (OUTPUT_DIR / "README.md").write_text(manifest, encoding="utf-8")


def main() -> None:
    ensure_output_dir()
    setup_style()
    customers, products, stores, sales = load_data()
    _ = products, stores

    plot_monthly_sales(sales)
    plot_category_sales(sales)
    plot_subcategory_sales(sales)
    plot_store_sales(sales)
    plot_payment_methods(sales)
    plot_weekday_sales(sales)
    plot_customer_age(customers)
    plot_order_value_distribution(sales)
    plot_discount_distribution(sales)
    plot_quantity_distribution(sales)
    plot_gender_sales(sales)
    plot_category_sales_pie(sales)
    plot_payment_methods_pie(sales)
    plot_category_margin(sales)
    write_manifest()

    print(f"Saved graphs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
