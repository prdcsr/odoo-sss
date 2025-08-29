# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Stock Equipment",
    'summary': "Use discount coupons in sales orders",
    'description': """Integrate coupon mechanism in sales orders.""",
    'category': 'Sales/Sales',
    'version': '1.0',
    'depends': ['stock', 'sale_coupon'],
    'data': [
        # 'views/stock_equipment_program_views.xml',
        'views/stock_picking_views.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'license': 'LGPL-3',
}
