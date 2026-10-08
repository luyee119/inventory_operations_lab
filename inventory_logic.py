"""Inventory calculations. All numbers are illustrative until real data is supplied."""
from __future__ import annotations
import math
from datetime import date, timedelta
import pandas as pd

PRODUCT_COLUMNS = ["sku", "product_name", "category", "unit_cost", "initial_stock", "lead_time_days", "safety_stock", "target_cover_days"]
TRANSACTION_COLUMNS = ["date", "sku", "type", "quantity", "reference"]


class InventoryDataError(ValueError):
    """Input CSV is missing required columns or contains invalid records."""


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    missing = set(PRODUCT_COLUMNS) - set(df.columns)
    if missing:
        raise InventoryDataError(f"Products file missing columns: {', '.join(sorted(missing))}")
    out = df[PRODUCT_COLUMNS].copy()
    for col in ["sku", "product_name", "category"]:
        out[col] = out[col].astype("string").str.strip()
        if out[col].isna().any() or out[col].eq("").any():
            raise InventoryDataError(f"Products: {col} cannot be blank")
    if out["sku"].duplicated().any():
        raise InventoryDataError("Products: SKU values must be unique")
    for col in ["unit_cost", "initial_stock", "lead_time_days", "safety_stock", "target_cover_days"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
        if out[col].isna().any() or (out[col] < 0).any():
            raise InventoryDataError(f"Products: {col} must be a nonnegative number")
    for col in ["initial_stock", "lead_time_days", "safety_stock", "target_cover_days"]:
        if (out[col] % 1 != 0).any():
            raise InventoryDataError(f"Products: {col} must be a whole number")
        out[col] = out[col].astype(int)
    return out


def clean_transactions(df: pd.DataFrame, skus: set[str]) -> pd.DataFrame:
    missing = set(TRANSACTION_COLUMNS) - set(df.columns)
    if missing:
        raise InventoryDataError(f"Transactions file missing columns: {', '.join(sorted(missing))}")
    out = df[TRANSACTION_COLUMNS].copy()
    out["sku"] = out["sku"].astype("string").str.strip()
    out["type"] = out["type"].astype("string").str.strip().str.upper()
    if out["sku"].isna().any() or (~out["sku"].isin(skus)).any():
        raise InventoryDataError("Transactions contain missing or unknown SKUs")
    if (~out["type"].isin(["IN", "OUT"])).any():
        raise InventoryDataError("Transactions type must be IN or OUT")
    out["quantity"] = pd.to_numeric(out["quantity"], errors="coerce")
    if out["quantity"].isna().any() or (out["quantity"] <= 0).any() or (out["quantity"] % 1 != 0).any():
        raise InventoryDataError("Transaction quantities must be positive whole numbers")
    out["quantity"] = out["quantity"].astype(int)
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    if out["date"].isna().any():
        raise InventoryDataError("Transaction dates must be valid")
    out["reference"] = out["reference"].fillna("").astype(str)
    return out


def build_inventory(products: pd.DataFrame, transactions: pd.DataFrame, as_of: date | None = None, demand_window: int = 30) -> pd.DataFrame:
    """Initial stock is assumed to be at ledger start; transaction history is additive.

    Averages count OUT transactions in the last demand_window calendar days, including
    days with no orders. IN transactions do not count as demand.
    """
    if demand_window < 1:
        raise ValueError("demand_window must be >= 1")
    as_of = as_of or date.today()
    p = clean_products(products)
    t = clean_transactions(transactions, set(p["sku"]))
    future = t["date"].dt.date > as_of
    if future.any():
        raise InventoryDataError("Future-dated transactions are not supported")
    signed = t["quantity"].where(t["type"].eq("IN"), -t["quantity"])
    changes = signed.groupby(t["sku"]).sum()
    p["current_stock"] = p["initial_stock"] + p["sku"].map(changes).fillna(0).astype(int)
    if (p["current_stock"] < 0).any():
        affected = ", ".join(p.loc[p["current_stock"] < 0, "sku"].tolist())
        raise InventoryDataError(f"Negative resulting stock for SKU(s): {affected}. Check initial stock / transactions.")
    start = pd.Timestamp(as_of - timedelta(days=demand_window - 1))
    recent = t[(t["type"] == "OUT") & (t["date"] >= start)]
    outgoing = recent.groupby("sku")["quantity"].sum()
    p["units_out_window"] = p["sku"].map(outgoing).fillna(0).astype(int)
    p["avg_daily_demand"] = p["units_out_window"] / demand_window
    p["reorder_point"] = (p["avg_daily_demand"] * p["lead_time_days"] + p["safety_stock"]).apply(math.ceil)
    p["target_stock"] = (p["avg_daily_demand"] * (p["lead_time_days"] + p["target_cover_days"]) + p["safety_stock"]).apply(math.ceil)
    p["status"] = p.apply(lambda r: "REORDER" if r.current_stock <= r.reorder_point else "OK", axis=1)
    p["suggested_order_qty"] = p.apply(lambda r: max(0, int(r.target_stock-r.current_stock)) if r.status == "REORDER" else 0, axis=1)
    p["stock_value"] = (p["current_stock"] * p["unit_cost"]).round(2)
    p["days_of_cover"] = p.apply(lambda r: round(r.current_stock/r.avg_daily_demand,1) if r.avg_daily_demand>0 else None,axis=1)
    return p.sort_values(["status", "sku"], ascending=[True, True]).reset_index(drop=True)


def export_replenishment(inventory: pd.DataFrame) -> pd.DataFrame:
    cols = ["sku", "product_name", "current_stock", "avg_daily_demand", "lead_time_days", "safety_stock", "reorder_point", "target_stock", "suggested_order_qty"]
    return inventory.loc[inventory["suggested_order_qty"] > 0, cols].sort_values("suggested_order_qty", ascending=False).copy()
