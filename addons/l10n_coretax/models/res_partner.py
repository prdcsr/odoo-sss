# -*- coding: utf-8 -*- 

from odoo import api, fields, models
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class ResPartner(models.Model):
    _inherit = 'res.partner'

    country_code = fields.Char(related='country_id.code', string='Country Code')
    l10n_id_pkp = fields.Boolean(string="ID PKP", compute='_compute_l10n_id_pkp', store=True, readonly=False)
    l10n_id_nik = fields.Char(string='NIK', size=16, track_visibility=True)
    l10n_id_tax_address = fields.Char('Tax Address')
    l10n_id_tax_name = fields.Char('Tax Name')
    l10n_id_kode_transaksi = fields.Selection([
        ('01', '01 Kepada Pihak yang Bukan Pemungut PPN (Customer Biasa)'),
        ('02', '02 Kepada Pemungut Bendaharawan (Dinas Kepemerintahan)'),
        ('03', '03 Kepada Pemungut Selain Bendaharawan (BUMN)'),
        ('04', '04 DPP Nilai Lain (PPN 1%)'),
        ('05', '05 Besaran Tertentu'),
        ('06', '06 Penyerahan Lainnya (Turis Asing)'),
        ('07', '07 Penyerahan yang PPN-nya Tidak Dipungut (Kawasan Ekonomi Khusus/ Batam)'),
        ('08', '08 Penyerahan yang PPN-nya Dibebaskan (Impor Barang Tertentu)'),
        ('09', '09 Penyerahan Aktiva ( Pasal 16D UU PPN )'),
    ], string='Kode Transaksi', help='Dua digit pertama nomor pajak')

    vat16 = fields.Char(string='VAT 16', size=16, track_visibility=True, )
    vat = fields.Char(string='VAT', size=15, track_visibility=True)
    nitku_num = fields.Char(string='NITKU', size=6, track_visibility=True, default="000000")
    validated_identity = fields.Boolean(string='Validated Identity',default=False)

    @api.depends('vat', 'country_code')
    def _compute_l10n_id_pkp(self):
        for record in self:
            record.l10n_id_pkp = record.vat and record.country_code == 'ID'
