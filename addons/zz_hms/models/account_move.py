from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move' 

    operating_unit_id = fields.Char()

    def fp_string(self,string):
        if len(string) == 16:
            val=string[:3]+'.' +string[3:6]+'-'+string[6:8]+'.'+string[8:16]
        else: 
            val=string
        return val

    def _get_report_base_filename(self):
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Only invoices could be printed."))
        return self._get_move_display_name()
