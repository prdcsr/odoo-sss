{
  'name': 'Coretax ID',
  'author': 'SSS Group Dev',
  'version': '0.1',
  'depends': ['account', 'l10n_id','sale'],
  'data': [
    'views/account_move_view.xml',
    'views/res_company_view.xml',
    'views/res_partner_view.xml',
    'views/res_country_view.xml',
    'views/uom_uom_view.xml',
    'wizard/invoice_report_view.xml',
  ],
  'sequence': 3,
  'auto_install': False,
  'installable': True,
  'application': True,
  'category': 'GPM Odoo Addons',
  'summary': 'Odoo Addons Special For GPM Group',
  'license': 'OPL-1',
  'website': 'https://odoogpmid.galaxypartanimas.com/',
  'description': '-'
}
