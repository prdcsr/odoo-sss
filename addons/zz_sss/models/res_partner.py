# -*- coding: utf-8 -*- 

from odoo import api, fields, models
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    sequence_id = fields.Many2one('ir.sequence', string='RFQ Sequence',
                                  help="This field contains the information related to the numbering of the RFQ of this partner.",
                                  required=True, copy=False)
    vat = fields.Char(string='VAT', size=15, track_visibility=True)
    vat16 = fields.Char(string='VAT 16', size=16, track_visibility=True)
    l10n_id_nik = fields.Char(string='NIK', size=16, track_visibility=True)
    pa_sequence_id = fields.Many2one('ir.sequence', string='PA Sequence',
                                     help="This field contains the information related to the numbering of the PA of this partner.",
                                     copy=False)

    nitku_num = fields.Char(string='NITKU', size=6, track_visibility=True, default="000000")

    def npwp_string(self, string):
        if len(string) == 15:
            val = string[:2] + '.' + string[2:5] + '.' + string[5:8] + '.' + string[8:9] + '-' + string[
                                                                                                 9:12] + '.' + string[
                                                                                                               12:15]
        else:
            val = string
        return val

        # def _commercial_sync_to_children(self):

    #     commercial_partner = self.commercial_partner_id
    #     sync_vals = commercial_partner._update_fields_values(self._commercial_fields())
    #     sync_children = self.child_ids.filtered(lambda c: not c.is_company)
    #     for child in sync_children:
    #         child._commercial_sync_to_children()
    #     res = sync_children.write(sync_vals)
    #     sync_children._compute_commercial_partner()

    def _update_fields_values(self, fields):
        values = {}
        for fname in fields:
            field = self._fields[fname]
            if field.type == 'many2one':
                values[fname] = self[fname].id
            elif field.type == 'one2many':
                raise AssertionError(
                    'One2Many fields cannot be synchronized as part of `commercial_fields` or `address fields`')
            elif field.type == 'many2many':
                values[fname] = [(6, 0, self[fname].ids)]
            else:
                if fname not in ['vat', 'l10n_id_nik', 'l10n_id_pkp', 'phone', 'whatsapp', 'email']:
                    values[fname] = self[fname]
        return values
