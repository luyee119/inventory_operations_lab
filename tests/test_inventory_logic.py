from datetime import date
import pandas as pd
import pytest
from inventory_logic import build_inventory, InventoryDataError, export_replenishment

AS_OF = date(2026, 10, 7)

def samples(stock=20):
    p = pd.DataFrame([{"sku":"A", "product_name":"LED Bar", "category":"Lighting", "unit_cost":5,
        "initial_stock":stock,"lead_time_days":5,"safety_stock":10,"target_cover_days":5}])
    t = pd.DataFrame([{"date":"2026-10-06","sku":"A","type":"OUT","quantity":15,"reference":"order-1"},
        {"date":"2026-10-07","sku":"A","type":"IN","quantity":5,"reference":"receipt-1"}])
    return p,t

def test_calculations():
    p,t=samples()
    r=build_inventory(p,t,AS_OF,30).iloc[0]
    assert r.current_stock==10
    assert r.avg_daily_demand==0.5
    assert r.reorder_point==13
    assert r.target_stock==15
    assert r.suggested_order_qty==5
    assert r.stock_value==50

def test_no_reorder():
    p,t=samples(100)
    r=build_inventory(p,t,AS_OF,30).iloc[0]
    assert r.status=="OK" and r.suggested_order_qty==0
    assert export_replenishment(build_inventory(p,t,AS_OF,30)).empty

def test_invalid_sku():
    p,t=samples()
    t.loc[0,"sku"]="UNKNOWN"
    with pytest.raises(InventoryDataError,match="unknown SKUs"):
        build_inventory(p,t,AS_OF)

def test_negative_stock_rejected():
    p,t=samples(1)
    with pytest.raises(InventoryDataError,match="Negative"):
        build_inventory(p,t,AS_OF)

def test_future_transaction_rejected():
    p,t=samples()
    t.loc[0,"date"]="2026-10-08"
    with pytest.raises(InventoryDataError,match="Future"):
        build_inventory(p,t,AS_OF)

def test_zero_demand():
    p,t=samples(12)
    t=t.iloc[0:0].copy()
    r=build_inventory(p,t,AS_OF).iloc[0]
    assert r.avg_daily_demand == 0
    assert r.reorder_point==10
    assert r.suggested_order_qty==0
