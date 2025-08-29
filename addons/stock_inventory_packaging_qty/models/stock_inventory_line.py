# Copyright 2020 Camptocamp SA
# Copyright 2021 ForgeFlow, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    product_packaging = fields.Many2one(
        comodel_name="product.packaging",
        string="Package",
        domain="[('product_id', '=', product_id)]",
        # compute="_compute_packaging_auto",
        store=True,
    )
    product_packaging_qty = fields.Float(
        string="Package quantity",
        compute="_compute_product_packaging_qty",
        inverse="_inverse_product_packaging_qty",
        digits="Product Unit of Measure",
    )
    # @api.depends("product_id")
    # def _compute_packaging_auto(self):
    #     for line in self:
    #         if line.product_id:
    #             id = self.env["product.packaging"].search([("product_id","=",line.product_id.id)])
    #             line.product_packaging = id

    @api.depends(
        "product_qty", "product_uom_id", "product_packaging", "product_packaging.qty"
    )
    def _compute_product_packaging_qty(self):
        for line in self:
            if (
                    not line.product_packaging
                    or line.product_qty == 0
                    or line.product_packaging.qty == 0
            ):
                line.product_packaging_qty = 0
                continue
            # Consider uom
            if line.product_id.uom_id != line.product_uom_id:
                product_qty = line.product_uom_id._compute_quantity(
                    line.product_qty, line.product_id.uom_id
                )
            else:
                product_qty = line.product_qty
            line.product_packaging_qty = product_qty / line.product_packaging.qty

    def _prepare_product_packaging_qty_values(self):
        return {
            "product_qty": self.product_packaging.qty * self.product_packaging_qty,
            "product_uom_id": self.product_packaging.product_uom_id.id,
        }

    def _inverse_product_packaging_qty(self):
        for line in self:
            if line.product_packaging_qty and not line.product_packaging:
                raise UserError(
                    _(
                        "You must define a package before setting a quantity "
                        "of said package."
                    )
                )
            if line.product_packaging and line.product_packaging.qty == 0:
                raise UserError(
                    _("Please select a packaging with a quantity bigger than 0")
                )
            if line.product_packaging and line.product_packaging_qty:
                line.write(line._prepare_product_packaging_qty_values())

    @api.onchange("product_packaging")
    def _onchange_product_packaging(self):
        if self.product_packaging:
            self.update(
                {
                    "product_packaging_qty": 1,
                    "product_qty": self.product_packaging.qty,
                    "product_uom_id": self.product_id.uom_id,
                }
            )
        else:
            self.update({"product_packaging_qty": 0})
        if self.product_packaging:
            return self._check_package()

    @api.onchange("product_packaging_qty")
    def _onchange_product_packaging_qty(self):
        if self.product_packaging_qty and self.product_packaging:
            self.update(self._prepare_product_packaging_qty_values())

    @api.onchange("product_qty", "product_uom_id")
    def onchange_quantity(self):
        res = self._check_package()
        return res

    def _check_package(self):
        default_uom = self.product_id.uom_id
        pack = self.product_packaging
        qty = self.product_qty
        q = default_uom._compute_quantity(pack.qty, self.product_uom_id)
        if qty and q and round(qty % q, 2):
            newqty = qty - (qty % q) + q
            return {
                "warning": {
                    "title": _("Warning"),
                    "message": _(
                        "This product is packaged by %.2f %s. You should use %.2f %s."
                    )
                               % (pack.qty, default_uom.name, newqty, self.product_uom_id.name),
                },
            }
        return {}
