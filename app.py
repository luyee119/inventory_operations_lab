"""Inventory Operations Lab — two independent, synthetic demonstration workflows."""
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from inventory_logic import (
    InventoryDataError, build_inventory, clean_products,
    clean_transactions, export_replenishment,
)

BASE = Path(__file__).resolve().parent
st.set_page_config(page_title="Inventory Operations Lab", page_icon="📦", layout="wide")
st.title("📦 Inventory Operations Lab")
st.caption("Two independent workflows / 两个完全独立的业务模块")
st.warning("PUBLIC DEMO — All bundled records are synthetic, not real business records. Do not upload private business data to a public deployment.")

with st.sidebar:
    st.header("Business modules / 业务模块")
    module = st.radio(
        "Select a workflow / 选择业务",
        ["💡 Lighting Inventory & Replenishment / 灯具库存与补货", "🔌 EV Charger Returns / 充电桩退货管理"],
        key="business_module",
    )
    st.info("The modules use separate CSV files, metrics, analysis, and exports. No shared stock balances or cross-category replenishment.")

if module.startswith("💡"):
    st.header("💡 Lighting Inventory & Replenishment")
    st.caption("Forward inventory operations: inbound / outbound movements, inventory availability, replenishment planning.")
    with st.sidebar:
        st.subheader("Lighting data / 灯具数据")
        products_file = st.file_uploader("Lighting products CSV", type="csv", key="lighting_products")
        transactions_file = st.file_uploader("Lighting stock movements CSV", type="csv", key="lighting_movements")
        days = st.slider("Demand analysis window (days)", 7, 90, 30)
        analysis_date = st.date_input("Analysis date", value=date.today(), max_value=date.today())
        with st.expander("Required CSV columns"):
            st.code("Products: sku, product_name, category, unit_cost, initial_stock, lead_time_days, safety_stock, target_cover_days\nTransactions: date, sku, type, quantity, reference")
    if (products_file is None) != (transactions_file is None):
        st.error("Please upload both lighting CSVs together, or neither to use synthetic sample data.")
        st.stop()
    try:
        if products_file is None:
            products = pd.read_csv(BASE / "data" / "sample_products.csv", dtype={"sku": str})
            transactions = pd.read_csv(BASE / "data" / "sample_transactions.csv", dtype={"sku": str})
            st.caption("Source: synthetic lighting data")
        else:
            products = pd.read_csv(products_file, dtype={"sku": str})
            transactions = pd.read_csv(transactions_file, dtype={"sku": str})
            st.caption("Source: user-uploaded lighting CSVs, processed in this session")
        products = clean_products(products)
        transactions = clean_transactions(transactions, set(products["sku"]))
        inventory = build_inventory(products, transactions, as_of=analysis_date, demand_window=days)
    except (InventoryDataError, pd.errors.ParserError, UnicodeDecodeError, FileNotFoundError, ValueError, KeyError) as exc:
        st.error(f"Unable to process lighting inventory: {exc}")
        st.stop()

    a, b, c, d = st.columns(4)
    a.metric("Lighting SKUs", len(inventory))
    b.metric("Lighting units on hand", f"{inventory['current_stock'].sum():,}")
    c.metric("Lighting inventory value (USD)", f"${inventory['stock_value'].sum():,.2f}")
    d.metric("Lighting reorder alerts", int(inventory["status"].eq("REORDER").sum()))
    overview, detail, planning, methods = st.tabs(["📊 Lighting Overview", "📋 Lighting Stock Ledger", "🚨 Lighting Replenishment", "📘 Lighting Methodology"])
    with overview:
        st.subheader("Lighting stock by category")
        st.bar_chart(inventory.groupby("category")["current_stock"].sum())
        st.subheader("Lighting outbound demand by SKU")
        st.bar_chart(inventory.set_index("sku")["units_out_window"])
        st.caption(f"Outbound units within the {days}-day calendar window ending {analysis_date}.")
    with detail:
        st.subheader("Lighting inventory snapshot")
        visible = ["sku", "product_name", "category", "current_stock", "unit_cost", "stock_value", "units_out_window", "avg_daily_demand", "days_of_cover", "status"]
        st.dataframe(inventory[visible], use_container_width=True, hide_index=True)
        st.download_button("Export lighting inventory CSV", inventory.to_csv(index=False).encode("utf-8"), "lighting_inventory_snapshot.csv", "text/csv")
        st.subheader("Lighting IN / OUT movement ledger")
        st.dataframe(transactions.sort_values("date", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("Export lighting movement CSV", transactions.to_csv(index=False).encode("utf-8"), "lighting_stock_movements.csv", "text/csv")
    with planning:
        st.subheader("Lighting replenishment suggestions")
        st.caption("Rule-based suggestions, not orders. Does not include outstanding POs, reservations, or supplier minimums.")
        proposals = export_replenishment(inventory)
        if proposals.empty:
            st.success("No lighting SKUs trigger the reorder rule.")
        else:
            st.dataframe(proposals, use_container_width=True, hide_index=True)
        st.download_button("Export lighting replenishment CSV", proposals.to_csv(index=False).encode("utf-8"), "lighting_replenishment.csv", "text/csv")
        st.dataframe(inventory[["sku", "current_stock", "reorder_point", "target_stock", "suggested_order_qty", "status"]], use_container_width=True, hide_index=True)
    with methods:
        st.markdown("""### Lighting-specific calculations
- **Current stock** = initial stock + IN − OUT.
- **Average daily demand** = outbound quantity in selected N calendar days / N.
- **Reorder point** = ceil(daily demand × lead time + safety stock).
- **Target stock** = ceil(daily demand × (lead time + target cover days) + safety stock).
- **Suggested quantity** = max(0, target stock − current stock), only if stock ≤ reorder point.

These formulas only apply to **lighting inventory**. Charger returns are not added to lighting stock, demand, value, or replenishment.
""")
        st.download_button("Sample lighting products CSV", (BASE / "data" / "sample_products.csv").read_bytes(), "sample_lighting_products.csv", "text/csv")
        st.download_button("Sample lighting transactions CSV", (BASE / "data" / "sample_transactions.csv").read_bytes(), "sample_lighting_transactions.csv", "text/csv")
else:
    st.header("🔌 EV Charger Returns / 充电桩退货管理")
    st.caption("Reverse logistics only: returned units, product condition, disposition, storage, processing stages.")
    with st.sidebar:
        st.subheader("EV charger returns / 退货数据")
        upload = st.file_uploader("EV charger returns CSV", type="csv", key="charger_returns_upload")
        with st.expander("Required CSV columns"):
            st.code("return_id, order_reference, product_model, received_date, condition, disposition, quantity, days_in_storage, processing_stage")
    try:
        returns = pd.read_csv(upload if upload is not None else BASE / "data" / "sample_returns.csv")
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
        st.error(f"Unable to read charger returns: {exc}")
        st.stop()
    required = ["return_id", "order_reference", "product_model", "received_date", "condition", "disposition", "quantity", "days_in_storage", "processing_stage"]
    missing = sorted(set(required) - set(returns.columns))
    if missing:
        st.error("Missing returns fields: " + ", ".join(missing))
        st.stop()
    returns = returns[required].copy()
    returns["quantity"] = pd.to_numeric(returns["quantity"], errors="coerce")
    returns["days_in_storage"] = pd.to_numeric(returns["days_in_storage"], errors="coerce")
    returns["received_date"] = pd.to_datetime(returns["received_date"], errors="coerce")
    if (returns["quantity"].isna().any() or (returns["quantity"] <= 0).any()
        or (returns["quantity"] % 1 != 0).any() or returns["days_in_storage"].isna().any()
        or (returns["days_in_storage"] < 0).any() or returns["received_date"].isna().any()):
        st.error("Invalid charger return record. Quantity must be positive whole units; storage days nonnegative; dates valid.")
        st.stop()
    total = int(returns["quantity"].sum())
    restock = int(returns.loc[returns["disposition"] == "RESTOCK", "quantity"].sum())
    pending = total - restock
    a, b, c = st.columns(3)
    a.metric("EV charger returned units", f"{total:,}")
    b.metric("Marked for restock", f"{restock:,}")
    c.metric("Other dispositions", f"{pending:,}")
    overview, ledger, methods = st.tabs(["📊 Returns Overview", "📋 EV Charger Returns Ledger", "📘 Returns Methodology"])
    with overview:
        st.subheader("Return dispositions / 处理方式")
        st.bar_chart(returns.groupby("disposition")["quantity"].sum())
        st.subheader("Return conditions / 成色")
        st.bar_chart(returns.groupby("condition")["quantity"].sum())
        st.subheader("Processing stages / 处理进度")
        st.bar_chart(returns.groupby("processing_stage")["quantity"].sum())
        st.caption("Every chart here counts **EV charger returns only**, not lighting inventory.")
    with ledger:
        st.subheader("Charger returns register")
        st.dataframe(returns, hide_index=True, use_container_width=True)
        st.download_button("Export EV charger returns CSV", returns.to_csv(index=False).encode("utf-8"), "ev_charger_returns.csv", "text/csv")
    with methods:
        st.markdown("""### EV charger return rules
- **Received units** = sum of quantities in the returns register.
- **Marked for restock** = quantities with disposition `RESTOCK`; this is a **recorded disposition only**, not proof of electrical safety or approval for resale.
- **Other dispositions** = received units − marked for restock.
- Condition, processing stage, and disposition are separate fields.
- **No automatic transfer into salable inventory**; returned chargers require applicable inspection and safety procedures.
- Return rate is **not calculated** because shipment/sales denominator data is unavailable.
- This is independent of lighting replenishment; there is no combined stock or inventory value.
""")
        st.download_button("Sample EV charger returns CSV", (BASE / "data" / "sample_returns.csv").read_bytes(), "sample_ev_charger_returns.csv", "text/csv")
