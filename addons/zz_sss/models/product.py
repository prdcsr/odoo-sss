import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, RedirectWarning, ValidationError, UserError

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _default_operating_unit_ids(self):
        if self.categ_id and self.categ_id.operating_unit_ids:
            return [(6, 0, self.categ_id.operating_unit_ids.ids)]
        if self.env.user.default_operating_unit_id:
            return [
                (
                    6,
                    0,
                    [self.env["res.users"].operating_unit_default_get(self.env.uid).id],
                )
            ]

    @api.model
    def create(self, vals):
        # Check for duplicate default_code
        default_code = vals.get('default_code')
        if default_code:
            existing_product = self.env['product.template'].search([('default_code', '=', default_code)])
            if existing_product:
                raise UserError('A product with the same Internal Reference already exists.')

        return super(ProductTemplate, self).create(vals)

    @api.model
    def write(self, vals):
        if vals.get('default_code'):
            default_code = vals.get('default_code')
            if default_code:
                existing_product = self.env['product.template'].search([('default_code', '=', default_code)])
                if existing_product:
                    raise UserError('A product with the same Internal Reference already exists.')

        return super(ProductTemplate, self).write(vals)


    operating_unit_ids = fields.Many2many(
        "operating.unit",
        "product_operating_unit_rel",
        string="Operating Units",
        default=_default_operating_unit_ids,
    )

    akong_default_code = fields.Char('Akong Code')
    
    #state = fields.Selection([('Unit', 'Unit'), ('Sparepart', 'Sparepart'), ('Compressor', 'Compressor')], string="Status", default='Unit', track_visibility='always')
    
    #operating_unit_id = fields.Many2one(
    #    "operating.unit",
    #    string="Operating Unit"
    #)

    @api.constrains("operating_unit_ids", "categ_id")
    def _check_operating_unit(self):
        for record in self:
            if (
                record.operating_unit_ids and record.categ_id.operating_unit_ids
            ) and not all(
                ou in record.operating_unit_ids.ids
                for ou in record.categ_id.operating_unit_ids.ids
            ):
                raise ValidationError(
                    _(
                        "The operating units of the product must include the "
                        "ones from the category."
                    )
                )

    @api.onchange("categ_id")
    def onchange_operating_unit_ids(self):
        for record in self:
            if record.categ_id.operating_unit_ids:
                record.operating_unit_ids = [
                    (6, 0, record.categ_id.operating_unit_ids.ids)
                ]

class ProductCategory(models.Model):
    _inherit = "product.category"

    operating_unit_ids = fields.Many2many(
        "operating.unit",
        "product_category_operating_unit_rel",
        string="Operating Units",
    )

    def write(self, vals):
        res = super(ProductCategory, self).write(vals)
        product_template_obj = self.env["product.template"]
        if vals.get("operating_unit_ids"):
            for rec in self:
                products = product_template_obj.search(
                    [("categ_id", "child_of", rec.id)]
                )
                for product in products:
                    ou_ids = product.operating_unit_ids.ids
                    ou_ids.extend(vals.get("operating_unit_ids")[0][2])
                    product.operating_unit_ids = [(6, 0, ou_ids)]
        return res
