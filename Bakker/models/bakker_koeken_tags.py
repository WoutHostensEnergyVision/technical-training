from odoo import models, fields

class BakkerKoekenTags(models.Model):
    _name = "bakker_koeken_tags"
    _description = "Tags voor bakker koeken"

    name = fields.Char(string="Tag naam", required=True)
    color = fields.Char(string="Kleur", default="#3498db")  # Voor hex kleuren