from odoo import fields, models


class Location(models.Model):
    _inherit = "stock.location"

    repair_sequence = fields.Many2one('ir.sequence', string='Repair Sequence',
                                      help="This field contains the information related to the numbering of the repair of this location.",
                                      copy=False)
