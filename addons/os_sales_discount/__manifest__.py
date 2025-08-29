# -*-coding: utf-8 -*-
{
    'name': 'Odoo Discount For Sales',
    'version': '13.0.0.1',
    'summary': 'Odoo Discount For Sales',
    'author': 'Odosquare',
    'company': 'Odosquare',
    'maintainer': 'Odosquare',
    'category': 'Sales Management',
    'sequence': 4,
    'license': 'LGPL-3',
    'description': """Odoo Discount For Sales""",
    'images': ['static/description/Banner.png'],
    'depends': [
        'sale', 'sale_management'
    ],
    'data': [
        'report/sale_order_inherit.xml',
        'views/sales_discount.xml',

    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'applicable': True,
    'auto_install': True
}
