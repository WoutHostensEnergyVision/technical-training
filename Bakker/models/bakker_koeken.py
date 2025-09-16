from odoo import models, fields, api
from datetime import timedelta

class BakkerKoeken(models.Model):
    _name = "bakker_koeken"
    _description = "Bakker zijn lekkere koeken"

    name_koek = fields.Char(string="Naam van de koek", required=True, help="Vul hier de naam van de koek in")
    prijs_koek = fields.Float(string="Prijs van de koek", required=True, help="Vul hier de prijs van de koek in")
    voorraad_koek = fields.Integer(string="Voorraad van de koek", required=True , default=10)
    vervaldatum_koek = fields.Date(string="Vervaldatum van de koek", required=True, help="Vul hier de vervaldatum van de koek in", default=lambda self: fields.Date.today() + timedelta(days=30), readonly=True)
    aankoopdatum_koek = fields.Date(string="Aankoopdatum van de koek", default=fields.Date.today, help="Vul hier de aankoopdatum van de koek in", readonly=True)
    categorie_koek = fields.Selection(
        string="Categorie van de koek",
        selection=[
            ('chocolade', 'Chocolade'),
            ('fruit', 'Fruit'),
            ('noten', 'Noten'),
            ('speculaas', 'Speculaas'),
            ('pudding', 'Pudding'),
        ],
        required=True, help="Selecteer hier de categorie van de koek"
    )
    pudding_koek = fields.Boolean(string="Bevat pudding", default=False, help="Vink dit aan als de koek pudding bevat")
    totaal_inventarisatie = fields.Float(string="Totale inventarisatie waarde", compute="_compute_totaal_inventarisatie", store=True, readonly=True)
    
    @api.depends('prijs_koek', 'voorraad_koek')
    def _compute_totaal_inventarisatie(self):
        for record in self:
            record.totaal_inventarisatie = record.prijs_koek * record.voorraad_koek