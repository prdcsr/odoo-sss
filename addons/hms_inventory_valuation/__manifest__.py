{
    'name': 'FIFO Inventory Valuation',
    'version': '13.0.1.0.0',
    'summary': 'FIFO Inventory Valuation by Location and Date',
    'category': 'Inventory',
    'author': 'ChatGPT',
    'license': 'AGPL-3',
    'depends': ['stock'],
    'data': [
        'views/fifo_inventory_wizard_view.xml',
        'report/fifo_inventory_report_template.xml',
        'views/menu_items.xml',
        'report/report_fifo_inventory.xml'
    ],
    'installable': True,
    'application': False,
}
