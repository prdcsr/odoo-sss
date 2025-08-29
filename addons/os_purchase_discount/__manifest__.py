# -*- coding: utf-8 -*-

{
    'name': 'Odoo Discount For Purchases',
    'version': '13.0.0.1',	
    'summary': 'Odoo Discount For Purchases',
    'author': 'Odosquare',
    'company': 'Odosquare',
    'Maintainer': 'Odosquare',
    'sequence': 4,
    'images': ['static/description/banner.png'],
    'category': 'Purchase Management',
    'license': 'LGPL-3',
    'description': """Odoo Discount For Purchase""",
    'depends': [
        'purchase'
    ],
    'data': [
        'report/purchase_order_inherit.xml',
        'report/purchase_quotation_inherit.xml',
        'views/discount.xml',

    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,

}
