from odoo import models, fields, api


class LaundryWomp(models.Model):
    _name = 'laundry.womp'
    _description = 'Laundry Measurement'
    _order = 'id desc'

    order_line_id = fields.Many2one(
        'sale.order.line',
        required=True,
        ondelete='cascade'
    )

    measurement_type = fields.Selection([
        ('kg', 'Kilogram'),
        ('pcs', 'Pieces'),
    ], required=True)

    value = fields.Float(required=True)
    price_per_unit = fields.Float(required=True)
    subtotal = fields.Monetary(
        compute="_compute_subtotal",
        store=True
    )

    currency_id = fields.Many2one(
        related='order_line_id.currency_id',
        store=True
    )
    company_id = fields.Many2one(
        related='order_line_id.company_id',
        store=True
    )

    @api.depends('value', 'price_per_unit')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.value * rec.price_per_unit