{
    'name': 'Food Cost Detail Report',
    'version': '1.0',
    'category': 'Reporting',
    'summary': 'Creates a page where calculated food cost is shown.',
    'author': 'HMS',
    'depends': ['base', 'account', 'product', 'hms_restrict_user','web'],
    'data': [
        'wizard/food_cost_details.xml'
    ],
    'installable': True,
    'auto_install': False,
}
