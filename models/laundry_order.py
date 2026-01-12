# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

class LaundryOrder(models.Model):
    _name = 'laundry.order'
    _description = 'Laundry Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # =================================================================================
    # HEADER FIELDS
    # =================================================================================
    name = fields.Char(string='Laundry Order', required=True, copy=False, readonly=True, default='New')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    operator_id = fields.Many2one('hr.employee', string='Operator (PIC)', tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    invoice_id = fields.Many2one(comodel_name='account.move', string='No. Tagihan', readonly=True)
    
    # Date Fields
    date_received = fields.Datetime(string='Date Received', default=fields.Datetime.now, required=True, tracking=True)
    date_estimated = fields.Datetime(string='Estimated Finish', compute='_compute_date_estimated', store=True, readonly=False)
    date_finished = fields.Datetime(string='Finished Date', readonly=True, tracking=True)
    
    # Detail Info
    weight_kg = fields.Float(string='Weight (KG)', digits=(12, 2), tracking=True)
    qty_pcs = fields.Integer(string='Quantity (Pcs)', tracking=True)
    note = fields.Text(string='Notes')
    status_pembayaran = fields.Selection(string='Status Pembayaran', related='invoice_id.payment_state', store=True, groups="laundry.group_laundry_cashier,laundry.group_laundry_manager")
    delivery_alert = fields.Char(string='Alert', compute='_compute_delivery_alert', groups="laundry.group_laundry_cashier,laundry.group_laundry_manager")

    
    # New fields for View Logic
    invoice_payment_state = fields.Selection(related='invoice_id.payment_state', string="Payment Status", store=True)
    has_active_invoice = fields.Boolean(compute='_compute_has_active_invoice', string="Has Active Invoice")

    hide_operator_buttons = fields.Boolean(compute='_compute_button_visibility')
    hide_manager_buttons = fields.Boolean(compute='_compute_button_visibility')

    def _compute_button_visibility(self):
        # Check groups once for the user
        is_manager = self.env.user.has_group('laundry.group_laundry_manager')
        is_operator = self.env.user.has_group('laundry.group_laundry_operator')
        is_cashier = self.env.user.has_group('laundry.group_laundry_cashier')
        
        for rec in self:
            # Hide operator buttons if user is NOT an operator OR if they ARE a manager
            # Strict segregation: Managers should not do operator tasks.
            rec.hide_operator_buttons = not is_operator or is_manager
            
            # Hide manager/cashier buttons if user is NOT one of those
            # Cashiers still do Deliver and Payment
            rec.hide_manager_buttons = not (is_manager or is_cashier)

    @api.depends('invoice_id', 'invoice_id.state')
    def _compute_has_active_invoice(self):
        for rec in self:
            rec.has_active_invoice = bool(rec.invoice_id and rec.invoice_id.state != 'cancel')
    
    # =================================================================================
    # LINE & TOTAL
    # =================================================================================
    
    # 1. Master Field
    order_line_ids = fields.One2many('laundry.order.line', 'laundry_order_id', string='All Lines')

    # 2. View Fields (Filtered)
    line_laundry_ids = fields.One2many('laundry.order.line', 'laundry_order_id', string='Laundry Items', domain=[('product_id.is_laundry_service', '=', True)])
    line_additional_ids = fields.One2many('laundry.order.line', 'laundry_order_id', string='Produk Tambahan', domain=[('product_id.is_laundry_service', '=', False)])
    
    # 3. Computations
    total_amount = fields.Monetary(string='Total', compute='_compute_total', currency_field='currency_id', store=True, groups="laundry.group_laundry_cashier,laundry.group_laundry_manager")
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    
    @api.depends('order_line_ids.subtotal')
    def _compute_total(self):
        for record in self:
            record.total_amount = sum(record.order_line_ids.mapped('subtotal'))

    # Kategori Layanan
    category_service = fields.Selection([
        ('reguler', 'Reguler'), 
        ('express', 'Express')
    ], string='Kategori Layanan', compute='_compute_category_service', store=True)

    @api.depends('order_line_ids.product_id.category_service')
    def _compute_category_service(self):
        for rec in self:
            laundry_lines = rec.order_line_ids.filtered(lambda l: l.product_id.is_laundry_service)
            first_line = laundry_lines[:1]
            if first_line and first_line.product_id:
                rec.category_service = first_line.product_id.category_service
            else:
                rec.category_service = 'reguler'

    # Estimasi Waktu
    total_estimated_hours = fields.Float(string='Total Estimasi (Jam)', compute='_compute_total_estimated_hours', store=True)

    @api.depends('order_line_ids.product_id.estimated_hours', 'order_line_ids.quantity')
    def _compute_total_estimated_hours(self):
        for order in self:
            laundry_lines = order.order_line_ids.filtered(lambda x: x.product_id.is_laundry_service)
            total = sum(line.product_id.estimated_hours * line.quantity for line in laundry_lines)
            order.total_estimated_hours = total

    @api.depends('date_received', 'total_estimated_hours')
    def _compute_date_estimated(self):
        for order in self:
            if order.date_received:
                # Force float conversion & robust addition
                hours = float(order.total_estimated_hours or 0.0)
                order.date_estimated = order.date_received + timedelta(hours=hours)
            else:
                order.date_estimated = False
    
    @api.onchange('date_received', 'total_estimated_hours')
    def _onchange_recompute_estimated(self):
        self._compute_date_estimated()

    # =================================================================================
    # WORKFLOW STATE DEFINITION
    # =================================================================================
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

    state_statusbar = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('received', 'Received'),
        ('washing', 'Washing'),
        ('drying', 'Drying'),
        ('ironing', 'Ironing'),
        ('qc', 'Quality Check'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('cancel', 'Cancelled'),
    ], string='Status Bar', compute='_compute_state_statusbar')

    @api.depends('state')
    def _compute_state_statusbar(self):
        for rec in self:
            if rec.state == 'delivered':
                rec.state_statusbar = 'ready'
            else:
                rec.state_statusbar = rec.state

    # -------------------------------------------------------------------------
    # [LOGIC 1] MENENTUKAN ALUR (WORKFLOW)
    # -------------------------------------------------------------------------
    def _get_workflow_states(self):
        self.ensure_one()
        steps = ['draft', 'received']
        needs_wash = False
        needs_iron = False

        for line in self.order_line_ids:
            svc_type = line.product_id.laundry_service_type 
            if svc_type in ['cks', 'ck', 'carpet']:
                needs_wash = True
            if svc_type in ['cks', 'ironing']:
                needs_iron = True

        if needs_wash:
            steps.append('washing')
            steps.append('drying')
        if needs_iron:
            steps.append('ironing')

        steps.extend(['qc', 'ready', 'delivered'])
        return steps

    # -------------------------------------------------------------------------
    # [LOGIC 2] ACTION CONFIRM (Draft -> Received)
    # -------------------------------------------------------------------------
    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                continue
            
            # Validation: Ensure there are lines before confirming
            if not rec.order_line_ids:
                raise UserError(_("Order Laundry belum memiliki detail item! Tambahkan item terlebih dahulu."))

            rec.write({'state': 'received'})
            
        # Return the wizard for the first record in self to select operator
        if self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Pilih Operator',
                'res_model': 'laundry.assign.operator',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_order_id': self[0].id}
            }

    # -------------------------------------------------------------------------
    # [LOGIC 3] ACTION NEXT STAGE (Pindah Step)
    # -------------------------------------------------------------------------
    def action_next_stage(self):
        for rec in self:
            # A. VALIDASI OPERATOR
            if rec.state == 'received':
                if not rec.operator_id:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Siapa yang mengerjakan?',
                        'res_model': 'laundry.assign.operator',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {'default_order_id': rec.id}
                    }

            # B. STANDARD FLOW
            valid_steps = rec._get_workflow_states()
            if rec.state == 'delivered': continue
            if rec.state == 'cancel': raise UserError(_("Order Cancelled, cannot process."))

            try:
                current_idx = valid_steps.index(rec.state)
                if current_idx < len(valid_steps) - 1:
                    next_state = valid_steps[current_idx + 1]
                    
                    # ========================================================
                    # VALIDASI PEMBAYARAN
                    # ========================================================
                    if next_state == 'delivered':
                        if rec.status_pembayaran not in ['paid', 'in_payment']:
                            raise UserError(_(
                                "GAGAL SERAH TERIMA!\n\n"
                                "Barang tidak bisa diserahkan (Delivered) karena status pembayaran: %s.\n"
                                "Mohon lunasi tagihan terlebih dahulu."
                            ) % (dict(rec._fields['status_pembayaran']._description_selection(rec.env)).get(rec.status_pembayaran) or 'Belum Bayar'))
                    # ========================================================

                    # Log Waktu Jalan Disini
                    rec._on_state_change(next_state)
                    
                    rec.write({'state': next_state})
            except ValueError:
                raise UserError(_(f"Status '{rec.state}' tidak valid."))


    def _on_state_change(self, next_state):
        if next_state == 'qc':
            self._create_or_get_qc()
        elif next_state == 'ready':
            self.date_finished = fields.Datetime.now()

    # =================================================================================
    # MANUAL ACTIONS (BUTTON TRIGGERS)
    # =================================================================================

    def action_generate_invoice(self):
        self.ensure_one()
        invoice = self._create_invoice_logic()
        
        if invoice:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Customer Invoice',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': invoice.id,
            }
        else:
            # Jika invoice sudah ada, tampilkan warning atau buka invoice lama
            existing = self.env['account.move'].search([
                ('invoice_origin', '=', self.name),
                ('move_type', '=', 'out_invoice'),
                ('state', '!=', 'cancel')
            ], limit=1)
            if existing:
                 return {
                    'type': 'ir.actions.act_window',
                    'name': 'Customer Invoice',
                    'res_model': 'account.move',
                    'view_mode': 'form',
                    'res_id': existing.id,
                }

    # def action_print_laundry_tag(self):
    #     self.ensure_one()
    #     return self.env.ref('laundry.report_laundry_tag').report_action(self)

    # =================================================================================
    # INVOICE LOGIC
    # =================================================================================
    
    def _create_invoice_logic(self):
        if self.total_amount <= 0: return False

        # Cek Duplikat
        existing_inv = self.env['account.move'].search([
            ('invoice_origin', '=', self.name),
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel')
        ], limit=1)
        if existing_inv:
            self.invoice_id = existing_inv.id
            return existing_inv

        journal = self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', self.company_id.id)], limit=1)
        if not journal:
            raise UserError(_("Please define a Sale Journal for this company."))

        invoice_lines = []
        for line in self.order_line_ids:
            invoice_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'name': line.product_id.name,
                'tax_ids': [(6, 0, line.product_id.taxes_id.ids)],
            }))

        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'journal_id': journal.id,
            'invoice_line_ids': invoice_lines,
            'invoice_origin': self.name,
        }
        
        # 1. Create Invoice
        new_inv = self.env['account.move'].create(invoice_vals)
        
        # 2. AUTO POST (CONFIRM)
        new_inv.action_post()
        
        # 3. Link back to Order
        self.invoice_id = new_inv.id
        
        return new_inv


    def _create_or_get_qc(self):
        qc_obj = self.env['laundry.qc']
        if not qc_obj.search([('laundry_order_id', '=', self.id)], limit=1):
            qc_obj.create({'laundry_order_id': self.id})

    # =================================================================================
    # CRUD & HELPERS
    # =================================================================================
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

    def action_cancel(self): self.write({'state': 'cancel'})
    def action_draft(self): self.write({'state': 'draft'})

    def action_open_qc(self):
        self.ensure_one()
        return {
            'name': _('Quality Control Checklist'),
            'type': 'ir.actions.act_window',
            'res_model': 'laundry.order.qc.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id}
        }
    
    workflow_type = fields.Selection([
        ('full', 'Lengkap (CKS)'),
        ('wash', 'Cuci Kering (CK)'),
        ('iron', 'Setrika (Ironing)'),
    ], string='Workflow Type', compute='_compute_workflow_type')

    @api.depends('order_line_ids.product_id')
    def _compute_workflow_type(self):
        for rec in self:
            needs_wash = False
            needs_iron = False
            for line in rec.order_line_ids:
                st = line.product_id.laundry_service_type
                if st in ['cks', 'ck', 'carpet']: needs_wash = True
                if st in ['cks', 'ironing']: needs_iron = True
            
            if needs_wash and needs_iron: rec.workflow_type = 'full'
            elif needs_wash: rec.workflow_type = 'wash'
            elif needs_iron: rec.workflow_type = 'iron'
            else: rec.workflow_type = 'full'

    
    # =================================================================================
    # PAYMENT
    # =================================================================================

    def action_register_payment(self):
        self.ensure_one()
        invoices = self.env['account.move'].search([
            ('invoice_origin', '=', self.name),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial'))
        ])

        if not invoices:
            raise UserError(_("Tidak ditemukan tagihan pada Job Order ini"))


        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': invoices.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


    # =================================================================================
    # DELIVERY ALERT
    # =================================================================================

    @api.depends('state', 'invoice_payment_state')
    def _compute_delivery_alert(self):
        for rec in self:
            if rec.state == 'ready':
                # Cek pembayaran juga biar makin informatif
                if rec.invoice_payment_state == 'paid':
                    rec.delivery_alert = "✅ SIAP DIAMBIL (LUNAS)"
                else:
                    rec.delivery_alert = "⚠️ SIAP - BELUM LUNAS"
            else:
                rec.delivery_alert = False # Kosong jika bukan ready
                