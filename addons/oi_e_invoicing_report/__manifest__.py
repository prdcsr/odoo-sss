# -*- coding: utf-8 -*-
{
    'name': "E-Invoicing",

    'summary': """
                 Adds QR Code to invoices
        """,

    'description': """
        Adds QR Code to invoices and changes the invoice report template
    """,


    "author": "Openinside",
    "license": "OPL-1",
    'website': "https://www.open-inside.com",
    "price" : 0,
    "currency": 'EUR',
    'category': 'Accounting',
    "version": "13.0.0.0.1",

    # any module necessary for this one to work correctly
    'depends': ['account','portal'],

    # always loaded
    'data': ['views/report_invoice_document_custom.xml'],

    'odoo-apps' : True      
}