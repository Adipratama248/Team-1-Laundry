# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LaundryQC(models.Model):
    _name = "laundry.qc"
    _description = "Laundry Quality Control"
    _order = "approved_date desc"

    laundry_order_id = fields.Many2one(
        "laundry.order", string="Laundry Order", required=True, ondelete="cascade"
    )

    condition_before = fields.Text(string="Condition Before")
    condition_after = fields.Text(string="Condition After")

    approved_by = fields.Many2one("hr.employee", string="Approved By", required=True)
    approved_date = fields.Datetime(string="Approved Date", default=fields.Datetime.now)
    note = fields.Text(string="QC Notes")

    @api.model
    def create(self, vals):
        """Auto-update order state to 'ready' when QC is created"""
        result = super(LaundryQC, self).create(vals)
        result._update_order_to_ready()
        return result

    def write(self, vals):
        """Auto-update order state to 'ready' when QC is updated"""
        result = super(LaundryQC, self).write(vals)
        # Update state if approved_by or approved_date is set
        if "approved_by" in vals or "approved_date" in vals:
            self._update_order_to_ready()
        return result

    def _update_order_to_ready(self):
        """Update related laundry order state to 'ready' after QC"""
        for rec in self:
            if rec.laundry_order_id:
                # Use sudo to bypass access rights if needed
                rec.laundry_order_id.sudo().write({"state": "ready"})
