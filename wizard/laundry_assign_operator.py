# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LaundryAssignOperator(models.TransientModel):
    _name = 'laundry.assign.operator'
    _description = 'Assign Operator Laundry'

    order_id = fields.Many2one('laundry.order', string='Order', required=True)
    employee_id = fields.Many2one('hr.employee', string='Pilih Operator', required=True)

    def action_confirm(self):
        self.ensure_one()
        self.order_id.operator_id = self.employee_id
        return {'type': 'ir.actions.act_window_close'}