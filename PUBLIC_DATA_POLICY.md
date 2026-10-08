# Public data policy / 公开数据说明

**All three sample CSV files are generated from scratch with a fixed random seed.** They are NOT masked copies of the uploaded workbooks. They do not reuse actual item codes, quantities, fees, shipment dates, customer names, addresses, tracking IDs, or transactions. The broad concepts (lighting stock and EV charger returns) reflect the product domains, not the records.

## Private workbook assessment / 原始文件检查
- Lighting inventory workbook: multiple snapshots, outbound ledger, stock by box, product descriptions and notes. Potentially commercially sensitive product identifiers, movement quantities, shipment notes, and inventory levels.
- EV charger workbook: multi-period receiving and storage records, item models, condition classifications, storage/handling/shipping charges, disposition/scrap records, notes, and occasional personal names in shipment remarks.
- Never publish either source XLSX or raw screenshots, and never commit them into a Git repository.
- No public dataset is a factual aggregate of these business records. All public metrics are fictional for demonstration.

## Private deployment / 私有使用
If you later use genuine company data, do so only with permission, keep them outside Git, and apply explicit access controls. This demo has NO login or remote storage protection; do not upload confidential data to publicly deployed versions.

## Important data-model assumptions
- The returns dataset uses one unit per synthetic row; disposition status is sample classification, not a verified safety judgment.
- The stock replenishment module is a separate synthetic lighting inventory example and should not be automatically netted with EV charger returns.
- Fees are intentionally omitted from the public returns dataset.
