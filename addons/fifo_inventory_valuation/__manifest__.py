{
    "name": "FIFO Inventory Valuation",
    "version": "1.0",
    "category": "Inventory",
    "summary": "FIFO-based inventory valuation by date and location",
    "author": "Your Name",
    "depends": ["stock", "report_xlsx"],
    "data": [
        "views/fifo_valuation_views.xml",
        "report/fifo_valuation_report_template.xml"
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3"
}
