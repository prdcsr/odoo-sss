# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "Stock Packaging Qty",
    "summary": "Add packaging fields in the stock moves",
    "version": "13.0.1.1.1",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-warehouse",
    "category": "Warehouse",
    "depends": ["stock", "stock_move_packaging_qty"],
    "data": ["views/stock_inventory_line_view.xml","views/stock_inventory_form.xml"],
    "license": "LGPL-3",
    "installable": True,
}
