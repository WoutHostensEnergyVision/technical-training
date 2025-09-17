from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TestModel(models.Model):
    _name = "aaap.plaats"
    _description = "Test Model for AAAP"
    _order = "geboorte_datum desc, name asc"
    
    name = fields.Char()
    description = fields.Text()
    location = fields.Char(string="Location")
    
    status = fields.Selection([
        ('pasgeboren', 'Pasgeboren'),
        ('jong', 'Jong'),
        ('volwassen', 'Volwassen'),
        ('senior', 'Senior'),
        ('bejaard', 'Bejaard'),
        ('overleden', 'Overleden')
    ], string="Status", default='jong', compute="_compute_status", tracking=True)
    
    aantal_dagelijkse_bananen = fields.Integer(string="Aantal Dagelijkse Banen", )
    aantal_reeds_gegeten_bananen = fields.Integer(string="Aantal Reeds Gegeten Bananen", default=0, editable=False)
    geboorte_datum = fields.Date(string="Geboorte Datum", default='2000-01-01')
    geslacht = fields.Selection(
        selection=[("man", "Man"), ("vrouw", "Vrouw")],
        string="Geslacht",
        required=True
    )
    kleur = fields.Char(string="Kleur", default="#8B4513")
    dood = fields.Boolean(string="Dood", default=False)
    aantal_poten = fields.Integer(string="Aantal Poten", default=4)
    aantal_oren = fields.Integer(string="Aantal Oren", default=2)
    type_id = fields.Many2one(
        comodel_name="aaap.type",
        string="Type",
        help="Select the type of this model"
    )
    
    tag_ids = fields.Many2many(
        comodel_name="aaap.tag",
        relation="aaap_plaats_tag_rel",  
        column1="plaats_id",           
        column2="tag_id",               
        string="Tags",
        help="Select the tags associated with this model"
    )
    
    waardeprijs = fields.Float(string="Waardeprijs", compute="_compute_waardeprijs", _inverse="_inverse_waardeprijs", store=True)
    is_verkocht = fields.Boolean(string='Is Verkocht', compute='_compute_is_verkocht', store=True)
    factuur_ids = fields.One2many('account.move', 'aap_plaats_id', string='Facturen')
    laatste_factuur_id = fields.Many2one('account.move', string='Laatste Factuur', 
                                        compute='_compute_laatste_factuur', store=True)
    invoice_count = fields.Integer(compute='_compute_invoice_count', string='Aantal Facturen')

    aantal_bots = fields.Integer(string='Aantal Bots', default=0)
    click_multiplier = fields.Float(string='Click Multiplier', default=1.0)
    bananen_per_seconde = fields.Float(string='Bananen per Seconde', compute='_compute_bananen_per_seconde', store=True)
    laatste_bot_update = fields.Datetime(string='Laatste Bot Update', default=fields.Datetime.now)
    bot_level = fields.Integer(string='Bot Level', default=0)
    multiplier_level = fields.Integer(string='Multiplier Level', default=0)
    
    image_1920 = fields.Image(string="Aap Afbeelding", max_width=1920, max_height=1920)
    image_128 = fields.Image("Aap Thumbnail", related="image_1920", max_width=128, max_height=128, store=True)

    def action_dood_aap(self):
        for record in self:
            record.dood = True
            record.aantal_dagelijkse_bananen = 0
            record.status = 'overleden'
        return True
    
    def action_levende_aap(self):
        for record in self:
            record.dood = False
            if not record.aantal_dagelijkse_bananen:
                record.aantal_dagelijkse_bananen = 5
            record.waardeprijs = record.aantal_dagelijkse_bananen * 0.5 + record.aantal_poten * 10 + record.aantal_oren * 5
            record.waardeprijs = round(record.waardeprijs, 2)

            if record.geboorte_datum:
                today = fields.Date.today()
                age_days = (today - record.geboorte_datum).days
                if age_days < 365:  # Jonger dan 1 jaar
                    record.status = 'pasgeboren'
                elif age_days < 365 * 5:  # 1-5 jaar
                    record.status = 'jong'
                elif age_days < 365 * 15:  # 5-15 jaar
                    record.status = 'volwassen'
                elif age_days < 365 * 25:  # 15-25 jaar
                    record.status = 'senior'
                else:  # Ouder dan 25 jaar
                    record.status = 'bejaard'
            else:
                record.status = 'jong'  # Standaard status
        return True
    
    @api.depends('geboorte_datum')
    def _compute_status(self):
        for record in self:
            if record.geboorte_datum:
                        today = fields.Date.today()
                        age_days = (today - record.geboorte_datum).days
                        if age_days < 365:  # Jonger dan 1 jaar
                            record.status = 'pasgeboren'
                        elif age_days < 365 * 5:  # 1-5 jaar
                            record.status = 'jong'
                        elif age_days < 365 * 15:  # 5-15 jaar
                            record.status = 'volwassen'
                        elif age_days < 365 * 25:  # 15-25 jaar
                            record.status = 'senior'
                        else:  # Ouder dan 25 jaar
                            record.status = 'bejaard'
            else:
                record.status = 'jong'  # Standaard status
                
    @api.depends('aantal_dagelijkse_bananen', 'aantal_poten', 'aantal_oren')
    def _compute_waardeprijs(self):
        for record in self:
            record.waardeprijs = record.aantal_dagelijkse_bananen * 0.5 + record.aantal_poten * 10 + record.aantal_oren * 5
            record.waardeprijs = round(record.waardeprijs, 2)
            
    def _inverse_waardeprijs(self):
        for record in self: 
            record.aantal_dagelijkse_bananen = (record.waardeprijs - record.aantal_poten * 10 - record.aantal_oren * 5) / 0.5
            record.aantal_dagelijkse_bananen = int(record.aantal_dagelijkse_bananen)
            record.aantal_poten = (record.waardeprijs - record.aantal_dagelijkse_bananen * 0.5 - record.aantal_oren * 5) / 10
            record.aantal_poten = int(record.aantal_poten)
            record.aantal_oren = (record.waardeprijs - record.aantal_dagelijkse_bananen * 0.5 - record.aantal_poten * 10) / 5
            record.aantal_oren = int(record.aantal_oren)
            
    @api.onchange('dood')
    def _onchange_dood(self):
        if self.dood:
            self.waardeprijs = 0.0
            self.aantal_dagelijkse_bananen = 0
            self.status = 'overleden'
        else:
            self.waardeprijs = self.aantal_dagelijkse_bananen * 0.5 + self.aantal_poten * 10 + self.aantal_oren * 5
            self.waardeprijs = round(self.waardeprijs, 2)
            if not self.aantal_dagelijkse_bananen:
                self.aantal_dagelijkse_bananen = 5
                
    @api.constrains('aantal_dagelijkse_bananen', 'aantal_poten', 'aantal_oren')
    def _check_positive_values(self):
        for record in self:
            if record.aantal_dagelijkse_bananen < 0 or record.aantal_poten < 0 or record.aantal_oren < 0:
                raise ValidationError("Aantal dagelijkse bananen, poten en oren moeten positief zijn.")
            
    @api.constrains('geboorte_datum')
    def _check_geboorte_datum(self):
        for record in self:
            if record.geboorte_datum and record.geboorte_datum > fields.Date.today():
                raise ValidationError("Geboortedatum kan niet in de toekomst liggen.")
            
    @api.constrains('naam', 'description')
    def _check_unique_name_and_description(self):
        for record in self:
            if record.name and record.description:
                if len(record.name) < 3 or len(record.description) < 5:
                    raise ValidationError("Naam moet minimaal 3 tekens lang zijn en beschrijving minimaal 5 tekens lang.")
                if record.name == record.description:
                    raise ValidationError("Naam en beschrijving mogen niet gelijk zijn.")
            if not record.name or not record.description:
                raise ValidationError("Naam en beschrijving mogen niet leeg zijn.")
            existing_records = self.search([
                ('name', '=', record.name),
                ('description', '=', record.description),
                ('id', '!=', record.id)
            ])
            if existing_records:
                raise ValidationError("Naam en beschrijving moeten uniek zijn.")
            
    @api.constrains('waardeprijs')
    def _check_waardeprijs(self):
        for record in self:
            if record.waardeprijs < 32:
                raise ValidationError("Waardeprijs moet minimaal 32 zijn. Geef hem meer bananen!")
            
    @api.depends('factuur_ids')
    def _compute_laatste_factuur(self):
        for record in self:
            record.laatste_factuur_id = self.env['account.move'].search([
                ('aap_plaats_id', '=', record.id),
                ('state', '=', 'posted'),
                ('move_type', '=', 'out_invoice')
            ], order='invoice_date desc', limit=1)

    @api.depends('factuur_ids', 'factuur_ids.state')
    def _compute_is_verkocht(self):
        for record in self:
            record.is_verkocht = bool(self.env['account.move'].search_count([
                ('aap_plaats_id', '=', record.id),
                ('state', '=', 'posted'),
                ('move_type', '=', 'out_invoice')
            ]))
            
    @api.depends('factuur_ids')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.factuur_ids)

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': 'Facturen voor %s' % self.name,
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('aap_plaats_id', '=', self.id)],
            'context': {'create': False}
        }
        
    @api.depends('aantal_bots', 'bot_level')
    def _compute_bananen_per_seconde(self):
        for record in self:
            # Basis: elke bot produceert 0.1 bananen per seconde
            # Elke bot level verhoogt dit met 50%
            bot_efficiency = 0.1 * (1 + (record.bot_level * 0.5))
            record.bananen_per_seconde = record.aantal_bots * bot_efficiency
    
    def get_bot_cost(self):
        """Berekent de kosten voor de volgende bot (exponentieel stijgend)"""
        base_cost = 10
        return int(base_cost * (1.5 ** self.aantal_bots))
    
    def get_multiplier_upgrade_cost(self):
        """Berekent de kosten voor multiplier upgrade"""
        base_cost = 100
        return int(base_cost * (2 ** self.multiplier_level))
    
    def get_bot_upgrade_cost(self):
        """Berekent de kosten voor bot efficiency upgrade"""
        base_cost = 250
        return int(base_cost * (3 ** self.bot_level))   