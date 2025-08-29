from odoo import models, fields


class HrContractOvertime(models.Model):
    _inherit = 'hr.contract'

    over_hour = fields.Monetary('Upah per jam')
    over_day = fields.Monetary('Upah per hari')
    over_jabodetabek = fields.Monetary('Upah lembur Jabodetabek')

    outside_non_overnight = fields.Monetary('Upah dinas luar kota tidak menginap area 1')
    outside_non_overnight_far_area = fields.Monetary("Upah dinas luar kota tidak menginap area 2")
    rest_duration = fields.Float("Durasi istirahat lembur")