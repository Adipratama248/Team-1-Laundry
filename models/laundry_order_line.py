# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LaundryOrderLine(models.Model):
    _name = "laundry.order.line"
    _description = "Laundry Order Line"

    laundry_order_id = fields.Many2one(
        "laundry.order", string="Laundry Order", required=True, ondelete="cascade"
    )
    product_id = fields.Many2one(
        "product.product", string="Product / Service", required=True
    )
    is_laundry_service = fields.Boolean(
        string="Is Laundry Service", related="product_id.is_laundry_service", store=True
    )
    laundry_service_type = fields.Selection(
        string="Jenis Layanan", related="product_id.laundry_service_type", store=True
    )

    order_state = fields.Selection(
        string="Order State", 
        related="laundry_order_id.state", 
        store=True,
        readonly=True
    )

    # Related field to access parent order's state
    state = fields.Selection(
        string="Order State",
        related="laundry_order_id.state",
        store=False,
        readonly=True,
    )

    # Field untuk membedakan tipe line (laundry service vs additional product)
    line_type = fields.Selection(
        [("laundry", "Laundry Service"), ("additional", "Additional Product")],
        string="Line Type",
        required=True,
        default="laundry",
    )

    uom_id = fields.Many2one("uom.uom", string="Unit", required=True)
    quantity = fields.Float(string="Quantity", default=1.0)
    price_unit = fields.Float(
        string="Price",
        groups="laundry.group_laundry_cashier,laundry.group_laundry_manager",
    )
    subtotal = fields.Monetary(
        string="Subtotal",
        compute="_compute_subtotal",
        store=True,
        currency_field="currency_id",
        groups="laundry.group_laundry_cashier,laundry.group_laundry_manager",
    )
    currency_id = fields.Many2one(
        "res.currency", related="laundry_order_id.currency_id", readonly=True
    )
    note_in = fields.Char(
        string="Kondisi Awal (Cacat/Noda)",
        help="Catat jika ada noda, sobek, atau luntur sebelum dicuci.",
    )
    note_out = fields.Char(
        string="Kondisi Akhir (QC Note)",
        help="Catat hasil setelah proses (misal: Noda membandel tidak hilang).",
    )

    # (OPTIONAL) LINK KE SALES ORDER LINE
    sale_line_id = fields.Many2one("sale.order.line", string="Sales Order Line")

    @api.depends("quantity", "price_unit")
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit

    @api.onchange("product_id")
    def _onchange_product(self):
        if self.product_id:
            self.price_unit = self.product_id.lst_price
            self.uom_id = self.product_id.uom_id

            # Auto-set line_type based on product
            if self.product_id.is_laundry_service:
                self.line_type = "laundry"
            else:
                self.line_type = "additional"

    def action_open_condition_in(self):
        return {
            "name": "Kondisi Barang Masuk",
            "type": "ir.actions.act_window",
            "res_model": "laundry.condition",
            "view_mode": "form",
            "target": "new",
            "context": {"default_line_id": self.id},
        }

    # (OPTIONAL) LINK KE SALES ORDER LINE
    sale_line_id = fields.Many2one("sale.order.line", string="Sales Order Line")
