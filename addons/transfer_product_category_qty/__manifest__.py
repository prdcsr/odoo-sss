{
    'name': 'Transfer Product Category QTY',
    'author': 'SSS',
    'version': '1.0',
    'category': 'Operations/Inventory',
    'summary': 'Show product category qty in transfer',
    'description': '',
    'website': 'https://www.yasukapower.com',
    'depends': ['stock'],
    'data': [
        'views/assets_template.xml',
        'views/stock_picking_view.xml',
    ],
    'qweb': [
        'static/src/xml/category_summary_template.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False
}
