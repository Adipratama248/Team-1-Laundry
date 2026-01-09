from odoo import models, fields, api


class LaundryProcessLog(models.Model):
    _name = "laundry.process.log"
    _description = "Laundry Process Log"
    _order = "start_time desc"

    laundry_order_id = fields.Many2one(
        "laundry.order", string="Laundry Order", required=True, ondelete="cascade"
    )
    process_type = fields.Selection(
        [("washing", "Washing"), ("drying", "Drying"), ("ironing", "Ironing")],
        string="Process",
        required=True,
    )
    employee_id = fields.Many2one("hr.employee", string="Handled By", required=True)
    start_time = fields.Datetime(string="Start Time", default=fields.Datetime.now)
    end_time = fields.Datetime(string="End Time")
    duration = fields.Float(
        string="Duration (Hours)", compute="_compute_duration", store=True
    )
    note = fields.Text(string="Note")

    @api.depends("start_time", "end_time")
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                rec.duration = delta.total_seconds() / 3600
            else:
                rec.duration = 0.0

    @api.model
    def create(self, vals):
        result = super(LaundryProcessLog, self).create(vals)
        result._update_order_state()
        return result

    def write(self, vals):
        result = super(LaundryProcessLog, self).write(vals)
        if "process_type" in vals:
            self._update_order_state()
        return result

    def _update_order_state(self):
        """Update related laundry order state based on process type"""
        for rec in self:
            if rec.laundry_order_id and rec.process_type:
                # Use sudo to bypass access rights if needed
                rec.laundry_order_id.sudo().write({"state": rec.process_type})
