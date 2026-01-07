from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    laundry_order_id = fields.Many2one('laundry.order', string='Laundry Order', readonly=True)

    def action_confirm(self):
        res = super().action_confirm()

        for order in self:
            if not order.laundry_order_id:
                laundry_order = self.env['laundry.order'].create({
                    'partner_id': order.partner_id.id,
                    'sale_order_id': order.id,
                    'company_id': order.company_id.id,
                })
                order.laundry_order_id = laundry_order.id

                # Copy Sales Lines → Laundry Lines
                for line in order.order_line:
                    if line.product_id.type == 'service':
                        self.env['laundry.order.line'].create({
                            'laundry_order_id': laundry_order.id,
                            'product_id': line.product_id.id,
                            'uom_id': line.product_uom.id,
                            'quantity': line.product_uom_qty,
                            'price_unit': line.price_unit,
                            'sale_line_id': line.id,
                        })

        return res

    def action_open_laundry(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Laundry Order',
            'res_model': 'laundry.order',
            'view_mode': 'form',
            'res_id': self.laundry_order_id.id,
        }