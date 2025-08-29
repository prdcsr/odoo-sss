# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock Sales Report",
    "summary": "Add stock sales report on Inventory Reporting.",
    "version": "13.0.1.0.0",
    "category": "Warehouse",
    "author": "SSS",
    "license": "AGPL-3",
    "depends": ["stock", 'report_xlsx', 'report_xlsx_helper'],
    "data": [
        "wizard/stock_sales_report_wizard_view.xml",
        "report/stock_sales_report_xlsx.xml",
    ],
    "installable": True,
}
