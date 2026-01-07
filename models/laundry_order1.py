# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class LaundryOrder(models.Model):
    _name = 'laundry.order'
    _description = 'Laundry Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Laundry Order', required=True, copy=False, readonly=True, default='New')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    date_received = fields.Datetime(string='Date Received', default=fields.Datetime.now)
    date_estimated = fields.Datetime(string='Estimated Finish')
    date_finished = fields.Datetime(string='Finished Date', readonly=True)
    weight_kg = fields.Float(string='Weight (KG)', digits=(12, 2))
    qty_pcs = fields.Integer(string='Quantity (Pcs)')
    note = fields.Text(string='Notes')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('received', 'Received'),
        ('washing', 'Washing'),
        ('drying', 'Drying'),
        ('ironing', 'Ironing'),
        ('qc', 'Quality Check'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)


    line_laundry_ids = fields.One2many('laundry.order.line', 'laundry_order_id', string='Laundry Items', domain="[('product_id.is_laundry_service', '=', True)]")
    line_additional_ids = fields.One2many('laundry.order.line', 'laundry_order_id', string='Produk Tambahan', domain="[('product_id.is_laundry_service', '=', False)]")
    total_amount = fields.Monetary(string='Total', compute='_compute_total', currency_field='currency_id', store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)

    @api.depends('line_laundry_ids.subtotal', 'line_additional_ids.subtotal')
    def _compute_total(self):
        for record in self:
            record.total_amount = sum(record.line_laundry_ids.mapped('subtotal')) + sum(record.line_additional_ids.mapped('subtotal'))

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'laundry.order'
            ) or 'New'
        return super().create(vals)

    def action_received(self):
        self.state = 'received'

    def action_washing(self):
        self.state = 'washing'

    def action_drying(self):
        self.state = 'drying'

    def action_ironing(self):
        self.state = 'ironing'

    def action_qc(self):
        self.state = 'qc'
        # Create QC record if not exists
        if not self.env['laundry.qc'].search([('laundry_order_id', '=', self.id)]):
            self.env['laundry.qc'].create({
                'laundry_order_id': self.id,
            })

    def action_ready(self):
        self.state = 'ready'
        self.date_finished = fields.Datetime.now()

    def action_delivered(self):
        self.state = 'delivered'
        # Create invoice
        if self.total_amount > 0:
            journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
            invoice_vals = {
                'partner_id': self.partner_id.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'journal_id': journal.id if journal else False,
                'invoice_line_ids': [(0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'name': line.product_id.name,
                }) for line in self.line_ids],
            }
            self.env['account.move'].create(invoice_vals)

    def action_cancel(self):
        self.state = 'cancel'

    def action_open_qc(self):
        self.ensure_one()
        qc = self.env['laundry.qc'].search([('laundry_order_id', '=', self.id)], limit=1)
        if qc:
            return {
                'type': 'ir.actions.act_window',
                'name': 'QC',
                'res_model': 'laundry.qc',
                'view_mode': 'form',
                'res_id': qc.id,
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'QC',
                'res_model': 'laundry.qc',
                'view_mode': 'form',
                'context': {'default_laundry_order_id': self.id},
            }

    @api.constrains('weight_kg', 'qty_pcs')
    def _check_quantity(self):
        for rec in self:
            if rec.weight_kg < 0 or rec.qty_pcs < 0:
                raise UserError('Weight or Quantity cannot be negative!')

    
    # total_estimated_hours = fields.Float(string='Total Estimasi Waktu (Jam)', compute='_compute_total_estimated_hours', store=True)

    # @api.depends('line_laundry_ids.estimated_hours')
    # def _compute_total_estimated_hours(self):
    #     for order in self:
    #         order.total_estimated_hours = sum(order.line_laundry_ids.mapped('estimated_hours'))