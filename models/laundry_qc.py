# -*- coding: utf-8 -*-

from odoo import models, fields

class LaundryQC(models.Model):
    _name = 'laundry.qc'
    _description = 'Laundry Quality Control'
    _order = 'approved_date desc'

    laundry_order_id = fields.Many2one('laundry.order', string='Laundry Order', required=True, ondelete='cascade')

    condition_before = fields.Text(string='Condition Before')
    condition_after = fields.Text(string='Condition After')

    approved_by = fields.Many2one('hr.employee', string='Approved By', required=True)
    approved_date = fields.Datetime(string='Approved Date', default=fields.Datetime.now)
    note = fields.Text(string='QC Notes')