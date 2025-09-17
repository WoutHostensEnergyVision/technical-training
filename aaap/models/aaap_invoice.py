from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AaapInvoice(models.Model):
    _inherit = 'account.move'

    # Voeg een relatie toe naar aaap.plaats
    aap_plaats_id = fields.Many2one(
        comodel_name='aaap.plaats',
        string='Verkochte Aap',
        help='Selecteer een aap om te verkopen',
        domain=[('dood', '=', False)]
    )
    
    is_aaap_invoice = fields.Boolean(string='Is Aap Factuur', default=False)
    
    @api.onchange('aap_plaats_id')
    def _onchange_aap_plaats_id(self):
        if self.aap_plaats_id:
            self.is_aaap_invoice = True
            # Voeg automatisch een factuurlijn toe voor de aap
            invoice_line = self.env['account.move.line'].new({
                'name': f'Aap: {self.aap_plaats_id.name}',
                'quantity': 1,
                'price_unit': self.aap_plaats_id.waardeprijs,
            })
            self.invoice_line_ids = [(0, 0, {
                'name': f'Aap: {self.aap_plaats_id.name}',
                'quantity': 1,
                'price_unit': self.aap_plaats_id.waardeprijs,
                'tax_ids': [(6, 0, [])],  # Geen BTW
            })]

    def action_post(self):
        # Override de standaard post methode
        res = super(AaapInvoice, self).action_post()
        # Wanneer een aap-factuur is bevestigd, update de aap's status
        for invoice in self.filtered(lambda i: i.is_aaap_invoice and i.aap_plaats_id):
            # Controleer of de factuur een verkoopfactuur is
            if invoice.move_type == 'out_invoice' and invoice.state == 'posted':
                invoice.aap_plaats_id.write({
                    'dood': False,  # De aap leeft nog (hopelijk)
                    'location': f"Verkocht aan {invoice.partner_id.name}"
                })
        return res