# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LaundryOrderLine(models.Model):
    _name = 'laundry.order.line'
    _description = 'Laundry Order Line'

    laundry_order_id = fields.Many2one('laundry.order', string='Laundry Order', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product / Service', required=True)
    is_laundry_service = fields.Boolean(string='Is Laundry Service', related='product_id.is_laundry_service', store=True)
    laundry_service_type = fields.Selection(string='Jenis Layanan', related='product_id.laundry_service_type', store=True)
    
    # Field untuk membedakan tipe line (laundry service vs additional product)
    line_type = fields.Selection([
        ('laundry', 'Laundry Service'),
        ('additional', 'Additional Product')
    ], string='Line Type', required=True, default='laundry')
    
    uom_id = fields.Many2one('uom.uom', string='Unit', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Price')
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='laundry_order_id.currency_id', readonly=True)
    
    # (OPTIONAL) LINK KE SALES ORDER LINE
    sale_line_id = fields.Many2one('sale.order.line', string='Sales Order Line')
    
    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit

    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_id:
            self.price_unit = self.product_id.lst_price
            self.uom_id = self.product_id.uom_id
            
            # Auto-set line_type based on product
            if self.product_id.is_laundry_service:
                self.line_type = 'laundry'
            else:
                self.line_type = 'additional'

    # (OPTIONAL) LINK KE SALES ORDER LINE
    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Sales Order Line'
    )