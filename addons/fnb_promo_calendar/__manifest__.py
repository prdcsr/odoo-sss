# -*- coding: utf-8 -*-
{
    "name": "FNB Promotion & Holiday Scheduler",
    "summary": "Schedule promotions and holidays (data-only, no scope/discount)",
    "version": "13.0.1.0.0",
    "category": "Sales/Point of Sale",
    "author": "Your Company",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/promo_views.xml",
        "views/holiday_views.xml",
    ],
    "installable": True,
    "application": False,
}
