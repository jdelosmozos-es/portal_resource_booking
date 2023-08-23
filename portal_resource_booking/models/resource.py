from odoo import models, fields

class Space(models.Model):
    _name = 'calendar.event.location'
    _inherit = ["calendar.event.location", "image.mixin"]
    
    capacity = fields.Integer(required=True, default=0)
    note = fields.Text(
        'Description',
        help="Description of the space.")
    color = fields.Integer('Color')
    agendas = fields.One2many(comodel_name='booking.resource.agenda', inverse_name='space', string='Booking agenda')
#    bookings = fields.One2many(comodel_name='booking.booking', inverse_name='space', string='Bookings')
 
# TODO: Activar ésto por configuración, o mejor hacer que por defecto no quede marcada la opción Indefinido en la vista    
#    @api.model
    def get_resources(self, domain, date_start, date_end, filters):    
        res = super(Space, self).get_resources(domain, date_start, date_end, filters)
        results = []
        for record in res:
            if (record['id'] != False):
                results.append(record)
        return results