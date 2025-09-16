from odoo import models

class BakkerKoeken(models.Model):
    _name = "bakker_koeken"
    _description = "Bakker zijn lekkere koeken"

    name_koek = models.CharField(string="Naam van de koek", required=True)
    prijs_koek = models.Float(string="Prijs van de koek", required=True)
    voorraad_koek = models.Integer(string="Voorraad van de koek", required=True)