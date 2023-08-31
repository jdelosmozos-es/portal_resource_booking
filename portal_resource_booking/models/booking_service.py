from odoo import models, fields, api

class BookingService(models.Model):
    _name = 'booking.resource.service'
    _description = 'Object to group booking slots from an agenda depending on its space and type'
    _order = 'date'
    
    agenda = fields.Many2one(comodel_name='booking.resource.agenda', readonly=True, required=True, ondelete='restrict')
    date = fields.Date(required=True, readonly=True)
    type = fields.Many2one(comodel_name='booking.resource.agenda.type', related='agenda.type')
    space = fields.Many2one(comodel_name='calendar.event.location', related='agenda.space')
    slots = fields.One2many(comodel_name='booking.resource.agenda.slot', compute='_compute_slots')
    
    @api.depends('agenda','date')
    def _compute_slots(self):
        for record in self:
            record.slots = record.agenda.booking_slots.filtered(lambda x: x.start_datetime.date() == record.date)
    
    def name_get(self):
        result = []
        # DateTimeHelper = self.env['booking.datetime.helper']
        for record in self:
            # date = DateTimeHelper.get_user_datetime(record.start_datetime)
            result.append((record.id, '%s - %s [%s]' % (record.date, record.type.name,record.space.name)))
        return result