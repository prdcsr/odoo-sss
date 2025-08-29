{
    'name': 'Food Cost Report',
    'version': '1.0',
    'category': 'Reporting',
    'summary': 'Creates a page where calculated food cost is shown.',
    'author': 'HMS',
    'depends': ['base', 'account', 'product', 'mail', 'hms_restrict_user','daily_food_cost_report','web'],
    'data': [
        'views/food_cost_table_report.xml',
        'views/food_cost_report_qweb.xml',
        'wizard/food_cost_report_wizard.xml'
    ],
    'installable': True,
    'auto_install': False,
}
