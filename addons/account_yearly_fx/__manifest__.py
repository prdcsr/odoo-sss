# -*- coding: utf-8 -*-
{
    "name": "Yearly Currency Rate (Daily vs Yearly FX)",
    "version": "13.0.2.0.0",
    "summary": "Adds yearly FX rates per (Company, Currency, Year) and applies them to flagged accounts/journal entries; O2M on res.currency.",
    "author": "You + ChatGPT",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "views/menuitems.xml",
        "views/res_currency_yearly_rate_views.xml",
        "views/account_account_views.xml",
        "views/account_move_views.xml",
        "views/res_currency_views.xml",
        "reports/yearly_gl_report.xml",
        "reports/yearly_gl_templates.xml",
    ],
    "installable": True,
    "application": False,
}
