# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Inventory Comparison Report",
    "summary": "Add comparison report on Inventory adjustments vs inventory Report with multiple products.",
    "version": "1.0",
    "category": "Warehouse",
    "website": "-",
    "author": "HMS Developer",
    "license": "AGPL-3",
    "depends": ["stock", "date_range", "report_xlsx_helper"],
    "data": [
        'wizard/inventory_comparison_wizard.xml'
    ],
    "installable": True,
}
