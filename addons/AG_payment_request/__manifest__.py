# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'AG Payment Request',
    'version': '13.0',
    'category': 'Purchase Module',
    'author': 'APPSGATE FZC LLC',
    'Category':'HR',
    'website':'https://apps-gate.net',
    'summary': """
    This Module allows you to manage all type of expenses
    """,
    'description': """ 
            Payment
            Payment request

		Vendor payment, 
		Customer Payment,
	 	Request Payment,
		Payment,
		Payment request
		
     """,

    'depends': [
        'purchase','account',

    ],
    'data': [
        'security/ir.model.access.csv',
        'security/data.xml',
        'views/payment_request.xml',
        # 'views/res_config_settings_view.xml',
        'report/payment_request_report.xml',
        'report/report.xml'

    ],

    'images':[
        'static/src/img/main-screenshot.png'
    ],

    'license': 'AGPL-3',
    'installable': True,
    'price':'5',
    'currency':'USD',		
    'auto_install': False,
    'application': True,
}
