from ast import literal_eval

from odoo import api, fields, models
from odoo.tools import float_is_zero


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    costs_by_product = fields.Float(string='Cost By Finished Product', help='Specify cost of work center per Finished Product', default=0.0)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    operator_ids = fields.Many2many('hr.employee',string='Operator', copy=False)