# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

class LaundryOrder(models.Model):
    _name = 'laundry.order'
    _description = 'Laundry Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # --- Header Fields ---
    name = fields.Char(string='Laundry Order', required=True, copy=False, readonly=True, default='New')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    
    # --- Date Fields ---
    date_received = fields.Datetime(string='Date Received', default=fields.Datetime.now, required=True, tracking=True)
    date_estimated = fields.Datetime(string='Estimated Finish', compute='_compute_date_estimated', store=True, readonly=False)
    date_finished = fields.Datetime(string='Finished Date', readonly=True, tracking=True)
    
    # --- Detail Info ---
    weight_kg = fields.Float(string='Weight (KG)', digits=(12, 2), tracking=True)
    qty_pcs = fields.Integer(string='Quantity (Pcs)', tracking=True)
    note = fields.Text(string='Notes')
    category_service = fields.Selection([
        ('reguler', 'Reguler'), 
        ('express', 'Express')
    ], string='Kategori Layanan', compute='_compute_category_service', store=True)

    @api.depends('line_laundry_ids.product_id.category_service')
    def _compute_category_service(self):
        for rec in self:
            # Ambil baris pertama (index 0) sebagai referensi utama order ini
            # [:1] aman digunakan walau list kosong (tidak error index out of range)
            first_line = rec.line_laundry_ids[:1]
            
            if first_line and first_line.product_id:
                # Ambil value dari field yang sudah Anda buat di Product Inherit
                rec.category_service = first_line.product_id.category_service
            else:
                # Default jika belum ada produk dipilih
                rec.category_service = 'reguler'
                

    # --- Workflow State ---
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
    ], string='Status', default='draft', tracking=True, index=True)

    # --- Order Lines ---
    line_laundry_ids = fields.One2many('laundry.order.line', 'laundry_order_id', string='Laundry Items', domain="[('product_id.is_laundry_service', '=', True)]")
    line_additional_ids = fields.One2many('laundry.order.line', 'laundry_order_id', string='Produk Tambahan', domain="[('product_id.is_laundry_service', '=', False)]")
    
    # --- Financials ---
    total_amount = fields.Monetary(string='Total', compute='_compute_total', currency_field='currency_id', store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    
    # --- Computation for Estimations ---
    total_estimated_hours = fields.Float(string='Total Estimasi (Jam)', compute='_compute_total_estimated_hours', store=True)

    # ---------------------------------------------------------
    # COMPUTE METHODS
    # ---------------------------------------------------------

    @api.depends('line_laundry_ids.subtotal', 'line_additional_ids.subtotal')
    def _compute_total(self):
        for record in self:
            # Menggabungkan total dari jasa laundry dan produk tambahan (sabun, parfum, dll)
            record.total_amount = sum(record.line_laundry_ids.mapped('subtotal')) + sum(record.line_additional_ids.mapped('subtotal'))

    @api.depends('line_laundry_ids.product_id.estimated_hours', 'line_laundry_ids.quantity')
    def _compute_total_estimated_hours(self):
        for order in self:
            # Logic: Bisa sum (total jam) atau max (jam terlama). Di sini kita pakai sum.
            # Kita ambil dari field estimated_hours di product.template yang Anda buat sebelumnya
            total = sum(line.product_id.estimated_hours * line.quantity for line in order.line_laundry_ids)
            order.total_estimated_hours = total

    @api.depends('date_received', 'total_estimated_hours')
    def _compute_date_estimated(self):
        for order in self:
            if order.date_received and order.total_estimated_hours:
                # Menambahkan durasi jam ke waktu terima
                order.date_estimated = order.date_received + timedelta(hours=order.total_estimated_hours)
            elif not order.date_estimated:
                order.date_estimated = False

    # ---------------------------------------------------------
    # CRUD OVERRIDES
    # ---------------------------------------------------------

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('laundry.order') or 'New'
        return super().create(vals)

    @api.constrains('weight_kg', 'qty_pcs')
    def _check_quantity(self):
        for rec in self:
            if rec.weight_kg < 0 or rec.qty_pcs < 0:
                raise UserError(_('Weight or Quantity cannot be negative!'))

    # ---------------------------------------------------------
    # DYNAMIC WORKFLOW LOGIC (INTI PERUBAHAN)
    # ---------------------------------------------------------

    def _get_workflow_states(self):
        """
        Mengembalikan urutan status yang valid berdasarkan jenis layanan (product) yang dipilih.
        """
        self.ensure_one()
        steps = ['draft', 'received']
        
        needs_wash = False
        needs_iron = False

        # Loop semua line laundry untuk cek tipe service
        for line in self.line_laundry_ids:
            # Ambil field custom dari product.template
            svc_type = line.product_id.laundry_service_type 
            
            # Logic penentuan flow
            if svc_type in ['cks', 'ck', 'carpet']:
                needs_wash = True
            if svc_type in ['cks', 'ironing']:
                needs_iron = True

        # Susun flow
        if needs_wash:
            steps.append('washing')
            steps.append('drying')
        
        if needs_iron:
            steps.append('ironing')

        # Step akhir selalu ada
        steps.extend(['qc', 'ready', 'delivered'])
        return steps

    def action_next_stage(self):
        """
        Satu tombol untuk memajukan proses berdasarkan workflow dinamis.
        """
        for rec in self:
            valid_steps = rec._get_workflow_states()
            
            if rec.state == 'delivered':
                continue
            if rec.state == 'cancel':
                raise UserError(_("Order Cancelled, cannot process."))

            try:
                current_idx = valid_steps.index(rec.state)
                # Cek apakah ini step terakhir sebelum delivered
                if current_idx < len(valid_steps) - 1:
                    next_state = valid_steps[current_idx + 1]
                    
                    # --- Hooks / Trigger Logic saat pindah status ---
                    rec._on_state_change(next_state)
                    
                    # Update State
                    rec.write({'state': next_state})
            except ValueError:
                # Jika status saat ini tidak ada di valid_steps (misal data lama), force ke step logis terdekat
                raise UserError(_(f"Status '{rec.state}' tidak valid untuk alur layanan produk ini."))

    def _on_state_change(self, next_state):
        """
        Method khusus untuk menjalankan aksi saat status berubah.
        """
        # Trigger saat masuk ke QC
        if next_state == 'qc':
            self._create_or_get_qc()
        
        # Trigger saat Ready
        elif next_state == 'ready':
            self.date_finished = fields.Datetime.now()
            # Bisa kirim email notifikasi ke customer di sini
        
        # Trigger saat Delivered
        elif next_state == 'delivered':
            self._create_invoice()

    # ---------------------------------------------------------
    # HELPER ACTIONS
    # ---------------------------------------------------------

    def _create_or_get_qc(self):
        qc_obj = self.env['laundry.qc']
        if not qc_obj.search([('laundry_order_id', '=', self.id)], limit=1):
            qc_obj.create({'laundry_order_id': self.id})

    def _create_invoice(self):
        if self.total_amount <= 0:
            return

        journal = self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', self.company_id.id)], limit=1)
        if not journal:
            raise UserError(_("Please define a Sale Journal for this company."))

        # Gabungkan semua line (Laundry + Additional)
        invoice_lines = []
        all_lines = self.line_laundry_ids + self.line_additional_ids
        
        for line in all_lines:
            invoice_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.quantity, # Pastikan field quantity ada di model laundry.order.line
                'price_unit': line.price_unit, # Pastikan field price_unit ada
                'name': line.product_id.name,
                'tax_ids': [(6, 0, line.product_id.taxes_id.ids)], # Opsional: jika pakai pajak
            }))

        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'journal_id': journal.id,
            'invoice_line_ids': invoice_lines,
        }
        
        new_inv = self.env['account.move'].create(invoice_vals)
        
        # Opsional: Auto Post Invoice
        # new_inv.action_post()
        
        # Return action to view invoice (optional)
        return new_inv

    # ---------------------------------------------------------
    # BUTTON ACTIONS (UI)
    # ---------------------------------------------------------

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        # Reset jika perlu
        self.write({'state': 'draft'})

    def action_open_qc(self):
        self.ensure_one()
        qc = self.env['laundry.qc'].search([('laundry_order_id', '=', self.id)], limit=1)
        if qc:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Quality Check',
                'res_model': 'laundry.qc',
                'view_mode': 'form',
                'res_id': qc.id,
            }
        return False
    
    # ---------------------------------------------------------
    # workflow statusbar
    # ---------------------------------------------------------
    workflow_type = fields.Selection([
        ('full', 'Lengkap (CKS)'),
        ('wash', 'Cuci Kering (CK)'),
        ('iron', 'Setrika (Ironing)'),
    ], string='Workflow Type', compute='_compute_workflow_type')

    @api.depends('line_laundry_ids.product_id')
    def _compute_workflow_type(self):
        for rec in self:
            needs_wash = False
            needs_iron = False

            # Cek kebutuhan berdasarkan produk
            for line in rec.line_laundry_ids:
                st = line.product_id.laundry_service_type
                if st in ['cks', 'ck', 'carpet']:
                    needs_wash = True
                if st in ['cks', 'ironing']:
                    needs_iron = True
            
            # Tentukan tipe workflow
            if needs_wash and needs_iron:
                rec.workflow_type = 'full'      # Muncul semua
            elif needs_wash and not needs_iron:
                rec.workflow_type = 'wash'      # Skip Ironing
            elif not needs_wash and needs_iron:
                rec.workflow_type = 'iron'      # Skip Washing/Drying
            else:
                rec.workflow_type = 'full'      # Default fallback