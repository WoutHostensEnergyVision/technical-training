from odoo import models, fields, api
from odoo.exceptions import ValidationError

class BakkerVerkoop(models.Model):
    _name = "bakker_verkoop"
    _description = "Verkoop van bakkerij koeken"
    _order = "verkoop_datum desc"
    
    name = fields.Char(string="Verkoop Nummer", required=True, default="Nieuw")
    koek_id = fields.Many2one('bakker_koeken', string="Koek", required=True)
    klant_naam = fields.Char(string="Klant Naam", required=True)
    klant_email = fields.Char(string="Klant Email")
    klant_telefoon = fields.Char(string="Klant Telefoon")
    aantal = fields.Integer(string="Aantal", required=True, default=1)
    prijs_per_stuk = fields.Float(string="Prijs per stuk", required=True)
    korting_percentage = fields.Float(string="Korting (%)", default=0.0)
    subtotaal = fields.Float(string="Subtotaal", compute="_compute_totalen", store=True)
    korting_bedrag = fields.Float(string="Korting Bedrag", compute="_compute_totalen", store=True)
    totaal_bedrag = fields.Float(string="Totaal Bedrag", compute="_compute_totalen", store=True)
    verkoop_datum = fields.Datetime(string="Verkoop Datum", default=fields.Datetime.now)
    status = fields.Selection([
        ('concept', 'Concept'),
        ('bevestigd', 'Bevestigd'),
        ('betaald', 'Betaald'),
        ('geannuleerd', 'Geannuleerd')
    ], string="Status", default='concept')
    betaal_methode = fields.Selection([
        ('cash', 'Contant'),
        ('card', 'Bankkaart'),
        ('digital', 'Digitaal')
    ], string="Betaal Methode")
    opmerkingen = fields.Text(string="Opmerkingen")
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nieuw') == 'Nieuw':
            vals['name'] = self.env['ir.sequence'].next_by_code('bakker.verkoop') or f"VK{fields.Date.today().strftime('%Y%m%d')}-{len(self.search([]))}"
        return super().create(vals)
    
    @api.depends('aantal', 'prijs_per_stuk', 'korting_percentage')
    def _compute_totalen(self):
        for record in self:
            record.subtotaal = record.aantal * record.prijs_per_stuk
            record.korting_bedrag = record.subtotaal * (record.korting_percentage / 100)
            record.totaal_bedrag = record.subtotaal - record.korting_bedrag
    
    @api.constrains('aantal')
    def _check_voorraad(self):
        for record in self:
            if record.status == 'concept' and record.aantal > record.koek_id.voorraad_koek:
                raise ValidationError(f"Niet genoeg voorraad! Beschikbaar: {record.koek_id.voorraad_koek}")
    
    def action_bevestig_verkoop(self):
        """Bevestig de verkoop en update voorraad"""
        for record in self:
            if record.status != 'concept':
                raise ValidationError("Alleen concept verkopen kunnen bevestigd worden.")
            
            # Check voorraad nogmaals
            if record.aantal > record.koek_id.voorraad_koek:
                raise ValidationError(f"Niet genoeg voorraad! Beschikbaar: {record.koek_id.voorraad_koek}")
            
            # Update voorraad
            record.koek_id.voorraad_koek -= record.aantal
            record.status = 'bevestigd'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Verkoop Bevestigd!',
                'message': f'Verkoop {self.name} is bevestigd en voorraad is bijgewerkt',
                'type': 'success',
            }
        }
    
    def action_markeer_betaald(self):
        """Markeer als betaald"""
        for record in self:
            if record.status != 'bevestigd':
                raise ValidationError("Alleen bevestigde verkopen kunnen als betaald gemarkeerd worden.")
            record.status = 'betaald'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '💰 Betaling Ontvangen!',
                'message': f'Verkoop {self.name} is gemarkeerd als betaald',
                'type': 'success',
            }
        }
    
    def action_annuleer(self):
        """Annuleer verkoop en herstel voorraad"""
        for record in self:
            if record.status == 'betaald':
                raise ValidationError("Betaalde verkopen kunnen niet geannuleerd worden.")
            
            # Herstel voorraad als verkoop bevestigd was
            if record.status == 'bevestigd':
                record.koek_id.voorraad_koek += record.aantal
            
            record.status = 'geannuleerd'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '❌ Verkoop Geannuleerd',
                'message': f'Verkoop {self.name} is geannuleerd en voorraad is hersteld',
                'type': 'warning',
            }
        }

class BakkerVerkoopWizard(models.TransientModel):
    _name = 'bakker.verkoop.wizard'
    _description = 'Wizard voor het verkopen van koeken'
    
    koek_id = fields.Many2one('bakker_koeken', string='Koek', required=True)
    klant_naam = fields.Char(string='Klant Naam', required=True, default='Walk-in klant')
    klant_email = fields.Char(string='Klant Email')
    klant_telefoon = fields.Char(string='Klant Telefoon')
    aantal = fields.Integer(string='Aantal', required=True, default=1)
    prijs_per_stuk = fields.Float(string='Prijs per stuk', required=True)
    korting_percentage = fields.Float(string='Korting (%)', default=0.0)
    finale_prijs = fields.Float(string='Finale Prijs per stuk', compute='_compute_finale_prijs')
    totaal_bedrag = fields.Float(string='Totaal Bedrag', compute='_compute_totaal_bedrag')
    beschikbare_voorraad = fields.Integer(related='koek_id.voorraad_koek', string='Beschikbare Voorraad')
    direct_betaald = fields.Boolean(string='Direct Betaald', default=True)
    betaal_methode = fields.Selection([
        ('cash', 'Contant'),
        ('card', 'Bankkaart'),
        ('digital', 'Digitaal')
    ], string="Betaal Methode", default='cash')
    
    @api.depends('prijs_per_stuk', 'korting_percentage')
    def _compute_finale_prijs(self):
        for record in self:
            if record.korting_percentage:
                record.finale_prijs = record.prijs_per_stuk * (1 - record.korting_percentage / 100)
            else:
                record.finale_prijs = record.prijs_per_stuk
    
    @api.depends('aantal', 'finale_prijs')
    def _compute_totaal_bedrag(self):
        for record in self:
            record.totaal_bedrag = record.aantal * record.finale_prijs
    
    @api.constrains('aantal')
    def _check_voorraad(self):
        for record in self:
            if record.aantal > record.koek_id.voorraad_koek:
                raise ValidationError(f"Niet genoeg voorraad! Beschikbaar: {record.koek_id.voorraad_koek}")
    
    def action_verkoop(self):
        """Voer de verkoop uit"""
        verkoop = self.env['bakker_verkoop'].create({
            'koek_id': self.koek_id.id,
            'klant_naam': self.klant_naam,
            'klant_email': self.klant_email,
            'klant_telefoon': self.klant_telefoon,
            'aantal': self.aantal,
            'prijs_per_stuk': self.finale_prijs,
            'korting_percentage': self.korting_percentage,
            'betaal_methode': self.betaal_methode,
        })
        
        # Bevestig verkoop
        verkoop.action_bevestig_verkoop()
        
        # Markeer als betaald indien gewenst
        if self.direct_betaald:
            verkoop.action_markeer_betaald()
        
        return {
            'name': 'Nieuwe Verkoop',
            'type': 'ir.actions.act_window',
            'res_model': 'bakker_verkoop',
            'res_id': verkoop.id,
            'view_mode': 'form',
            'target': 'current',
        }