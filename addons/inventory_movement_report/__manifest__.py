# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Inventory Movement Report",
    "summary": "Add stock card report on Inventory Reporting with multiple products.",
    "version": "13.0.1.0.0",
    "category": "Warehouse",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "HMS Developer",
    "license": "AGPL-3",
    "depends": ["stock", "date_range", "report_xlsx_helper"],
    "data": [
        'report/report_action_inventory_movement.xml',
        'report/report_inventory_movement.xml',
        'wizard/inventory_movement_wizard.xml'
    ],
    "installable": True,
}
