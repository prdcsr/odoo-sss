# -*- coding: utf-8 -*- 

from odoo import api, fields, models
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
 
    sequence_id = fields.Many2one('ir.sequence', string='RFQ Sequence',
        help="This field contains the information related to the numbering of the RFQ of this partner.", required=True, copy=False)