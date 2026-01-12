from odoo import models, fields, api

class LaundryCondition(models.TransientModel):
    _name = 'laundry.condition'
    _description = 'Wizard Kondisi Barang'

    line_id = fields.Many2one('laundry.order.line', string='Line Referensi')
    
    # Checklist
    is_torn = fields.Boolean(string='Sobek / Bolong')
    torn_note = fields.Char(string='Lokasi Sobek', help="Contoh: Lengan Kiri, Kerah")
    
    is_stain = fields.Boolean(string='Bernoda')
    stain_type = fields.Selection([
        ('tinta', 'Tinta'),
        ('minyak', 'Minyak/Oli'),
        ('darah', 'Darah'),
        ('karat', 'Karat'),
        ('lain', 'Lainnya'),
    ], string='Jenis Noda')
    
    is_faded = fields.Boolean(string='Luntur / Pudar')
    is_button_missing = fields.Boolean(string='Kancing Hilang')
    
    additional_note = fields.Text(string='Catatan Tambahan')

    def action_save_condition(self):
        self.ensure_one()

        if not self.line_id:
            return {'type': 'ir.actions.act_window_close'}

        order = self.line_id.laundry_order_id

        # Cari atau buat QC
        qc = self.env['laundry.qc'].search(
            [('laundry_order_id', '=', order.id)],
            limit=1
        )
        if not qc:
            qc = self.env['laundry.qc'].create({
                'laundry_order_id': order.id
            })

        # Bangun catatan kondisi
        notes = []

        if self.is_torn:
            det = f" ({self.torn_note})" if self.torn_note else ""
            notes.append(f"Sobek{det}")

        if self.is_stain:
            jenis = dict(self._fields['stain_type'].selection).get(self.stain_type, '')
            notes.append(f"Noda: {jenis}")

        if self.is_faded:
            notes.append("Luntur")

        if self.is_button_missing:
            notes.append("Kancing Hilang")

        if self.additional_note:
            notes.append(self.additional_note)

        summary = " | ".join(notes) if notes else "Tidak ada catatan"

        # Format per item
        line_label = self.line_id.product_id.display_name or "Item"
        new_entry = f"- {line_label}: {summary}"

        # APPEND ke condition_before (bukan replace)
        qc.condition_before = (
            (qc.condition_before + "\n" if qc.condition_before else "")
            + new_entry
        )

        # Tetap simpan ke line (opsional, tapi kamu sudah pakai)
        self.line_id.note_in = summary

        return {'type': 'ir.actions.act_window_close'}
