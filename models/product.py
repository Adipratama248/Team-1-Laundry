from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_laundry_service = fields.Boolean(
        string="Laundry Service"
    )

    laundry_billing_type = fields.Selection([
        ('kg', 'Per KG'),
        ('pcs', 'Per PCS'),
        ('flat', 'Flat Price'),
    ])

    brand_name = fields.Char()
    product_type_laundry = fields.Selection([
        ('clothes', 'Clothes'),
        ('blanket', 'Blanket'),
        ('other', 'Other'),
    ])
    size_label = fields.Char()
    is_consumable_laundry = fields.Boolean(
        string="Laundry Consumable"
    )

    laundry_consumable_lines = fields.One2many(
        'product.consumable.line',
        'product_id',
        string='Laundry Consumables'
    )


class ProductConsumableLine(models.Model):
    _name = 'product.consumable.line'
    _description = 'Product Consumable Line'

    product_id = fields.Many2one('product.product', string='Service Product', required=True)
    consumable_id = fields.Many2one('product.product', string='Consumable', required=True, domain=[('is_consumable_laundry', '=', True)])
    quantity = fields.Float(string='Quantity', default=1.0, required=True)