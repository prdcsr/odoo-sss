# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sale Product Report',
    'version': '1.0',
    'category': 'Sales/Sales',
    'summary': 'Product Report for Salesman',
    'description': """
Reinvoice Employee Expense
==========================

Create some products for which you can re-invoice the costs.
This module allow to reinvoice employee expense, by setting the SO directly on the expense.
""",
    'depends': ['sale_management', 'product', 'sale'],
    'data': [
        "wizard/product_stock_report_wizard_view.xml",
        "wizard/product_sale_report_wizard_view.xml",
        "menuitems.xml",
        "reports.xml",
        "report/templates/layouts.xml",
        "report/templates/sale_product_stock.xml",
        "report/templates/product_sale.xml",

    ],
    "qweb": ["static/src/xml/report.xml"],
    'test': [],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
