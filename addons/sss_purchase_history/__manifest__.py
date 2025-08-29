{
    "name": "Purchase History",
    "version": "13.0.1.0.0",
    "depends": ["purchase_requisition", "report_xlsx", "purchase"],
    "author": "ChatGPT",
    "category": "Purchases",
    "description": "Track and report status and quantity changes in purchase requisitions",
    "data": [
        "security/ir.model.access.csv",
        "views/requisition_history_tree_view.xml",
        "views/order_history_tree_view.xml",
        "views/purchase_requisition_form_inherit.xml",
        "views/purchase_order_form_inherit.xml",
    ],
    "installable": True,
    "application": False
}
