# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Vendor Pricelist Product Specification',
    'category': 'Vendor Pricelist',
    'description': """
Product Specification in Vendor Pricelist
""",
    'version': '1.0',
    'depends': ['product', 'purchase_requisition'],
    'data': [
        'views/vendor_pricelist.xml',
        'report/factory_purchase_agreement.xml',

    ],
    'demo': [],
    'auto_install': False,
    'license': 'LGPL-3',
}
