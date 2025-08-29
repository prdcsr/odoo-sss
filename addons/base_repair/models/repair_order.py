# Copyright 2021 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RepairOrder(models.Model):

    _inherit = "repair.order"

    date_repair = fields.Datetime(
        "Repair Date",
        default=fields.Datetime.now,
        copy=False,
        help="Date of the repair, this field " "and user_id defines the calendar",
    )
    date_start_repair = fields.Datetime(
        "Repair Start Date",
        default=fields.Datetime.now,
        copy=False,
        help="Start Date of the repair",
    )
    
    date_end_repair = fields.Datetime(
        "Repair Start Date",
        default=fields.Datetime.now,
        copy=False,
        help="End Date of the repair",
    )

    duration = fields.Float("Estimated Repair Duration", help="Duration in hours and minutes.")
