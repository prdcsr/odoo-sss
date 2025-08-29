from ast import literal_eval

from odoo import api, fields, models
from odoo.tools import float_is_zero

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    costs_by_product = fields.Float(string='Cost By Finished Product', help='Specify cost of work center per Finished Product', default=0.0)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    operator_ids = fields.Many2many('res.users','mrp_users_rel', string='Operator', copy=False)
    technician_ids = fields.Many2many('res.users','mrp_technician_users_rel', string='Technician', copy=False)
    requester_id = fields.Many2one('res.users',string='Request By', copy=False)
