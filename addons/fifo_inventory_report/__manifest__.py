{
    'name': 'FIFO Inventory Valuation Report',
    'version': '13.0.1.0.0',
    'summary': 'Inventory valuation report per location with FIFO method',
    'category': 'Inventory',
    'author': 'Your Company',
    'depends': ['stock', 'product', 'base'],
    'data': [
        'views/fifo_inventory_wizard_view.xml',
        'views/fifo_inventory_template.xml',
    ],
    'installable': True,
    'application': False,
}