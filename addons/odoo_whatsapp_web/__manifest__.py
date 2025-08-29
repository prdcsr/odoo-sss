# -*- coding: utf-8 -*-
{
    'name': "Odoo Whatsapp Web",
    'version': '13.0.1',
    'summary': 'This module is used to send msg on whatsapp web',
    'sequence': -100,
    'description': """This module is used to send msg on whatsapp web""",
    'category': 'Discuss',
    'author': "HamdanERP Ltd.",
    'maintainer': 'HamdanERP',
    'website': 'https://www.hamdanerp.com',
    'license': 'AGPL-3',
    'depends': ['mail', 'account', 'base'],
    'data': [
        'views/odoo_whatsapp_web.xml',
        'views/whatsapp_icon_chat.xml',
    ],
    'images': ['static/description/banner6.gif'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
