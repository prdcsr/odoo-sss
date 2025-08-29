{ 
    'name': 'Daily Food Cost Report',
    'version': '13.0.1.0.0',
    'category': 'Reporting',
    'summary': 'Generates and emails a daily food cost report grouped by product and analytic account.',
    'author': 'ChatGPT',
    'depends': ['base', 'account', 'product', 'mail', 'hms_restrict_user', 'web'],
    'data': [
        'views/report_template.xml',
        'views/product_template.xml',
        'views/report_action.xml',
        'data/mail_template.xml',
        'data/cron_job.xml',
    ],
    'installable': True,
    'auto_install': False,
}
