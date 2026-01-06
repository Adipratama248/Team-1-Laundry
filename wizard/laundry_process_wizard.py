# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class LaundryProcessWizard(models.TransientModel):
    _name = 'laundry.process.wizard'
    _description = 'Laundry Process Wizard'

    laundry_order_id = fields.Many2one(
        'laundry.order',
        string='Laundry Order',
        required=True,
        default=lambda self: self._get_default_laundry_order()
    )

    process_type = fields.Selection([
        ('washing', 'Washing'),
        ('drying', 'Drying'),
        ('ironing', 'Ironing'),
    ], string='Process Type', required=True, default=lambda self: self._get_default_process_type())

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    start_time = fields.Datetime(string='Start Time', default=fields.Datetime.now, required=True)
    note = fields.Text(string='Note')

    def _get_default_laundry_order(self):
        return self.env.context.get('active_id')

    def _get_default_process_type(self):
        state = self.laundry_order_id.state
        state_map = {
            'received': 'washing',
            'washing': 'drying',
            'drying': 'ironing',
        }
        return state_map.get(state)

    def action_start_process(self):
        self.ensure_one()
        log_vals = {
            'laundry_order_id': self.laundry_order_id.id,
            'process_type': self.process_type,
            'employee_id': self.employee_id.id,
            'start_time': self.start_time,
            'note': self.note,
        }
        self.env['laundry.process.log'].create(log_vals)
        # Move stock for consumables
        self._move_consumables()
        # Update state
        self.laundry_order_id.write({'state': self._get_next_state()})
        return {'type': 'ir.actions.act_window_close'}

    def _move_consumables(self):
        for line in self.laundry_order_id.line_ids:
            for consumable in line.product_id.laundry_consumable_lines:
                move_vals = {
                    'name': f'Laundry Consumable for {self.laundry_order_id.name}',
                    'product_id': consumable.consumable_id.id,
                    'product_uom_qty': consumable.quantity * line.quantity,
                    'product_uom': consumable.consumable_id.uom_id.id,
                    'location_id': self.env.ref('stock.stock_location_stock').id,
                    'location_dest_id': self.env.ref('stock.stock_location_scrapped').id,  # or consumption location
                    'origin': self.laundry_order_id.name,
                }
                self.env['stock.move'].create(move_vals).action_confirm()

    def _get_next_state(self):
        state_map = {
            'washing': 'washing',
            'drying': 'drying',
            'ironing': 'ironing',
        }
        return state_map.get(self.process_type, self.laundry_order_id.state)