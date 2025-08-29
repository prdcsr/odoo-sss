from odoo import fields, models


class OpenItemsReportWizard(models.TransientModel):
    _inherit = "open.items.report.wizard"

    operating_unit_id = fields.Many2one(
        comodel_name="operating.unit",
        string="Operating Unit",
    )

    salesperson_id = fields.Many2one(
        comodel_name="res.users",
        string="Salesperson",
        domain=[('share', '=', False)],  # Only internal users
        help="Filter by salesperson from invoices and sale orders"
    )

    child_partners_only = fields.Boolean(
        string="Child Partners Only",
        default=True,
        help="Show only child partners (contacts) instead of parent companies"
    )

    date_to = fields.Date(
        string="Date To",
        help="Show transactions up to and including this date"
    )

    def _prepare_report_open_items(self):
        self.ensure_one()
        data = super()._prepare_report_open_items()
        data["operating_unit_id"] = self.operating_unit_id.id if self.operating_unit_id else False
        data["salesperson_id"] = self.salesperson_id.id if self.salesperson_id else False
        data["child_partners_only"] = self.child_partners_only
        data["date_to"] = self.date_to or False
        return data