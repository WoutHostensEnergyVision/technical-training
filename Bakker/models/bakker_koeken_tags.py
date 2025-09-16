from django.db import models

from odoo import models, fields

class BakkerKoekenTags(models.Model):
    _name = "bakker_koeken_tags"
    _description = "Tags voor bakker koeken"

    name = fields.Char(string="Tag naam", required=True)
    color = fields.Integer(string="Kleur")

    def __str__(self):
        return self.name