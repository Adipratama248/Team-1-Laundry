from odoo import models, fields


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    laundry_role = fields.Selection([
        ('operator', 'Operator'),
        ('kasir', 'Kasir'),
        ('gudang', 'Gudang'),
        ('admin', 'Admin'),
    ])

    laundry_active = fields.Boolean(default=True)