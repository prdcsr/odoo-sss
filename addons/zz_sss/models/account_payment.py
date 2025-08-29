
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from collections import defaultdict

class account_payment(models.Model):
    _inherit = "account.payment"

    check_date_due = fields.Date(string='Due Date', readonly=True, index=True, copy=False,
        states={'draft': [('readonly', False)]})
    
    """def _prepare_payment_moves(self):
        #for payment in self:            
        res = super(account_payment, self)._prepare_payment_moves()
        for payment in self:
            if payment.check_date_due:
                for move in res:
                    for line in move['line_ids']:
                        line['date_maturity'] = payment.check_date_due
        return res"""                                                      