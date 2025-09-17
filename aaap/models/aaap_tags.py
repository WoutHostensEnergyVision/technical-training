from odoo import models, fields, api

class AaapTag(models.Model):
    _name = 'aaap.tag'
    _description = 'Aap Tags'
    _order = 'name asc'

    name = fields.Char(string='Naam', required=True)
    color = fields.Integer(string='Kleur Index')
    category = fields.Selection([
        ('uiterlijk', 'Uiterlijk'),
        ('gedrag', 'Gedrag'),
        ('dieet', 'Dieet'),
    ], string='Categorie')
    
    aap_plaats_ids = fields.Many2many(
        'aaap.plaats',
        relation='aaap_plaats_tag_rel',
        column1='tag_id',
        column2='plaats_id',
        string='Gekoppelde Apen'
    )
    
    aantal_apen = fields.Integer(string='Aantal Apen', compute='_compute_aantal_apen')
    
    @api.depends('aap_plaats_ids')
    def _compute_aantal_apen(self):
        for tag in self:
            tag.aantal_apen = len(tag.aap_plaats_ids)
            
    def action_view_apen(self):
        self.ensure_one()
        return {
            'name': f'Apen met tag {self.name}',
            'view_mode': 'list,form',
            'res_model': 'aaap.plaats',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.aap_plaats_ids.ids)],
            'context': {'create': False}
        }