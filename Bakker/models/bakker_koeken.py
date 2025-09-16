from odoo import models, fields

class BakkerKoeken(models.Model):
    _name = "bakker_koeken"
    _description = "Bakker zijn lekkere koeken"

    name_koek = fields.Char(string="Naam van de koek", required=True)
    prijs_koek = fields.Float(string="Prijs van de koek", required=True)
    voorraad_koek = fields.Integer(string="Voorraad van de koek", required=True)
    vervaldatum_koek = fields.Date(string="Vervaldatum van de koek", required=True)
    categorie_koek = fields.Selection(
        string="Categorie van de koek",
        selection=[
            ('chocolade', 'Chocolade'),
            ('fruit', 'Fruit'),
            ('noten', 'Noten'),
            ('speculaas', 'Speculaas'),
        ],
        required=True,
    )
    pudding_koek = fields.Boolean(string="Bevat pudding", default=False)