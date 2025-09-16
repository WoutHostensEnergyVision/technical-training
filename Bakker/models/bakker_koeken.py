from odoo import models, fields

class BakkerKoeken(models.Model):
    _name = "bakker_koeken"
    _description = "Bakker zijn lekkere koeken"

    name_koek = fields.Char(string="Naam van de koek", required=True)
    prijs_koek = fields.Float(string="Prijs van de koek", required=True)
    voorraad_koek = fields.Integer(string="Voorraad van de koek", required=True)