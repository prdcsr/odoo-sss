# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Sales Dashboard',
    'version': '13.0.0.9',
    'sequence': 1,
    'category': 'sales',
    'summary': 'Sales Dashboard',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.technaureus.com/',
    'description': """This module is for Sales Dashboard""",
    'depends': ['sale_management'],
    'price': '',
    'currency': '',
    'license': 'Other proprietary',
    'data': [
        'views/sales_dashboard_views.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        "static/src/xml/sales_dashboard.xml",
    ],
    'images': ['images/main_screenshot.png'],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
