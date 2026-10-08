# Inventory Operations Lab 📦

**A portfolio / interview MVP built with Python, Pandas and Streamlit.**

> **Disclaimer / 免责声明:** This is an independent educational prototype inspired by inventory operations. It has **not** been implemented or deployed at any company. All bundled inventory data, SKUs, orders, suppliers and prices are **synthetic**. It is not a production ERP system, nor an AI predictive model. Never commit real customer, supplier, pricing or shipping information without authorization.

## Two independent product workflows / 两个独立品类

The app uses a **sidebar module selector**. These are separate datasets and calculations, not subdivisions of a shared inventory:

1. **Lighting Inventory & Replenishment / 灯具库存与补货**: products and stock movements, stock availability, historical outbound demand, reorder points, replenishment proposals, and lighting-specific CSV exports.
2. **EV Charger Returns / 充电桩退货管理**: return receiving, condition, disposition, storage days, processing stages, and EV charger-only CSV export.

**No combined dashboard, SKU pool, inventory value, stock movement ledger, or replenishment logic.** Charger returns are never automatically counted as lighting stock or as resalable stock. All data is entirely fabricated for the public demo. No company names or original business files are distributed.

## Features / 功能

- Import paired product and stock-movement CSV files / 导入产品及库存流水 CSV
- Track stock via starting inventory + inbound − outbound / 计算实时库存快照
- Analyze outbound demand over 7–90 calendar days / 分析历史出库量
- Flag low stock using lead times and safety stock / 触发补货预警
- Generate transparent, rules-based replenishment proposals / 生成补货建议
- View charts and export full inventory and replenishment CSVs / 图表和 CSV 导出

## Run locally / 本地运行

Requires Python **3.10+**.

**Windows (PowerShell):**

```powershell
cd inventory_operations_lab
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If PowerShell blocks activation, run without activating:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

**macOS/Linux:**

```bash
cd inventory_operations_lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

A local browser page usually opens at **http://localhost:8501**. Stop it with `Ctrl+C` in the terminal.

## Demo steps for an interview / 面试演示

1. Open the app: the bundled *fictional* inventory is already loaded.
2. Select **Lighting Inventory & Replenishment**; show the lighting-only stock chart and stock value.
3. Open **Inventory Detail**, highlight stock movement records.
4. Open **Replenishment**, explain reorder point and order quantity.
5. Download the replenishment CSV.
6. Switch to **EV Charger Returns** and demonstrate the separate return-condition/disposition dashboard and CSV export.
7. Explain that it is a **prototype**, not implemented in company operations.

## Input data dictionary / 数据格式

**Products CSV** (`data/sample_products.csv`):

| Column | Meaning |
|---|---|
| `sku` | unique identifier / 唯一 SKU |
| `product_name` | display name |
| `category` | category |
| `unit_cost` | cost per unit, **USD** |
| `initial_stock` | beginning balance **before all imported transactions** |
| `lead_time_days` | supplier lead time in calendar days |
| `safety_stock` | buffer units |
| `target_cover_days` | extra cover days beyond the lead time for target stock |

**Transactions CSV** (`data/sample_transactions.csv`):

| Column | Meaning |
|---|---|
| `date` | ISO date e.g. `2026-10-07` |
| `sku` | matches products table |
| `type` | `IN` or `OUT` |
| `quantity` | strictly positive whole-number units |
| `reference` | free-text synthetic transaction ID |

**Critical:** `initial_stock` is the beginning balance, not the current balance. All transactions are applied to the beginning balance. Using today's actual inventory in `initial_stock` and loading old outbound records again would double-count them.

## Planning logic / 补货模型

Let `D` = total OUT units in the last N calendar days / N (including zero-outbound days), `L` = lead time, `SS` = safety stock, `C` = additional target cover days, and `Q` = current stock.

- `Reorder point = ceil(D × L + SS)`
- `Target stock = ceil(D × (L + C) + SS)`
- If `Q <= reorder point`, `Suggested quantity = max(0, target stock − Q)`, else zero.
- `Stock value = Q × unit cost`.

For example: `D=10/day`, `L=7 days`, `SS=20 units`, `C=5 days`, `Q=50`. Reorder point is **90**, target stock is **140**, and suggested order is **90 units**. These are hypothetical numbers.

## Project limitations / 局限

No persistent database, shipping integrations, user accounts, purchase-order tracking, reserved stock, lost-sales tracking, supplier minimums, forecast model, or real-time multi-user editing. Inventory demand is proxied by `OUT` transactions, which could underestimate demand during stockouts. The rules demonstrate planning concepts, not validated optimal purchasing decisions.

## Tests / 测试

`pytest` is optional development dependency (not required to run the dashboard).

```bash
python -m pip install pytest
python -m pytest -q
```

## Suggested honest interview description / 面试描述

"I built an independent Python and Streamlit inventory-planning prototype inspired by my hands-on inventory experience. It reads synthetic stock-movement records, calculates stock on hand and historical outbound demand, and proposes rule-based replenishment quantities. It is an educational MVP, not a system deployed at company."


## Returns management expansion / 退货管理扩展

The **EV Charger Returns** sidebar module presents fictional EV charger returns. Upload an optional CSV with columns `return_id,order_reference,product_model,received_date,condition,disposition,quantity,days_in_storage,processing_stage` or use the bundled `data/sample_returns.csv`. Review counts and export the displayed dataset.

**Privacy warning:** All bundled datasets are entirely synthetic, not anonymized originals. See `PUBLIC_DATA_POLICY.md`. Do NOT upload actual customer or company files to publicly hosted instances.
