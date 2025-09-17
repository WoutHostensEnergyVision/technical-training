from odoo import models, fields

class AaapType(models.Model):
    _name = 'aaap.type'
    _description = 'AAAP Type'
    _order = 'name asc'
    
    name = fields.Char(string='Type Name', required=True)

class AaapModel(models.Model):
    _name = 'aaap.model'
    _description = 'AAAP Model'

    type_id = fields.Many2one('aaap.type', string='Type')
    