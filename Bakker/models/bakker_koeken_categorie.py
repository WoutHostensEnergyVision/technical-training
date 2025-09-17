from odoo import models, fields

class BakkerKoekenCategorie(models.Model):
    _name = "bakker_koeken_categorie"
    _description = "Categorieën voor bakker koeken"

    name = fields.Char(string="Categorie naam", required=True)
    beschrijving = fields.Text(string="Beschrijving")
    actief = fields.Boolean(string="Actief", default=True)