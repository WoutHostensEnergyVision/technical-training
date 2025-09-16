from odoo import models, fields
from datetime import timedelta

class BakkerKoeken(models.Model):
    _name = "bakker_koeken"
    _description = "Bakker zijn lekkere koeken"

    name_koek = fields.Char(string="Naam van de koek", required=True, help="Vul hier de naam van de koek in")
    prijs_koek = fields.Float(string="Prijs van de koek", required=True, help="Vul hier de prijs van de koek in")
    voorraad_koek = fields.Integer(string="Voorraad van de koek", required=True , default=10)
    vervaldatum_koek = fields.Date(string="Vervaldatum van de koek", required=True, help="Vul hier de vervaldatum van de koek in", default=lambda self: fields.Date.today() + timedelta(days=10))
    categorie_koek = fields.Selection(
        string="Categorie van de koek",
        selection=[
            ('chocolade', 'Chocolade'),
            ('fruit', 'Fruit'),
            ('noten', 'Noten'),
            ('speculaas', 'Speculaas'),
        ],
        required=True, help="Selecteer hier de categorie van de koek"
    )
    pudding_koek = fields.Boolean(string="Bevat pudding", default=False, help="Vink dit aan als de koek pudding bevat")