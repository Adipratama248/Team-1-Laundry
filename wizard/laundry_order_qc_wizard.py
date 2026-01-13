# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LaundryOrderQCWizard(models.TransientModel):
    _name = "laundry.order.qc.wizard"
    _description = "Laundry Order QC Wizard"

    order_id = fields.Many2one("laundry.order", string="Order", required=True)

    # Checklist
    clean_check = fields.Boolean(string="Bersih / Tidak ada Noda", default=False)
    dry_check = fields.Boolean(string="Kering Sempurna", default=False)
    iron_check = fields.Boolean(string="Setrika Rapi", default=False)
    perfume_check = fields.Boolean(string="Sudah Diberi Parfum", default=False)
    qty_check = fields.Boolean(string="Jumlah Sesuai (Pcs/Kg)", default=False)

    note = fields.Text(string="Catatan Tambahan")
    condition_after = fields.Text(string="Kondisi Setelah Laundry")

    def action_confirm_qc(self):
        self.ensure_one()

        # All checks must be true (usually)
        if not all(
            [
                self.clean_check,
                self.dry_check,
                self.iron_check,
                self.perfume_check,
                self.qty_check,
            ]
        ):
            raise UserError(_("Semua poin QC harus dicentang untuk melanjutkan."))

        # Create or update QC record
        qc_obj = self.env["laundry.qc"]
        qc_vals = {
            "laundry_order_id": self.order_id.id,
            "clean_check": self.clean_check,
            "dry_check": self.dry_check,
            "iron_check": self.iron_check,
            "perfume_check": self.perfume_check,
            "qty_check": self.qty_check,
            "note": self.note,
            "approved_by": (
                self.env.user.employee_id.id
                if hasattr(self.env.user, "employee_id")
                else False
            ),
            "approved_date": fields.Datetime.now(),
        }

        existing_qc = qc_obj.search(
            [("laundry_order_id", "=", self.order_id.id)], limit=1
        )
        if existing_qc:
            existing_qc.write(qc_vals)
        else:
            qc_obj.create(qc_vals)

        # Move order to ready
        self.order_id.action_next_stage()

        return {"type": "ir.actions.act_window_close"}
