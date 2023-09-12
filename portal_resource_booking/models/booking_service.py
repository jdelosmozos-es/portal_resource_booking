from odoo import models, fields, api

class BookingService(models.Model):
    _name = 'booking.resource.service'
    _description = 'Object to group booking slots from an agenda depending on its space and type'
    _order = 'date'
    
    agenda = fields.Many2one(comodel_name='booking.resource.agenda', readonly=True, required=True, ondelete='cascade')
    date = fields.Date(required=True, readonly=True)
    type = fields.Many2one(comodel_name='booking.resource.agenda.type', related='agenda.type')
    space = fields.Many2one(comodel_name='calendar.event.location', related='agenda.space')
    slots = fields.One2many(comodel_name='booking.resource.agenda.slot', compute='_compute_slots')
    is_open_online = fields.Boolean(readonly=True,default=True)
    
    @api.model
    def get_is_closed(self):
        return True if not self.is_open_online else False
        
    @api.depends('agenda','date')
    def _compute_slots(self):
        for record in self:
            record.slots = record.agenda.booking_slots.filtered(lambda x: x.start_datetime.date() == record.date)
    
    def name_get(self):
        result = []
        # DateTimeHelper = self.env['booking.datetime.helper']
        for record in self:
            # date = DateTimeHelper.get_user_datetime(record.start_datetime)
            result.append((record.id, '%s - %s [%s]' % (record.date.strftime('%d/%m/%Y'),record.type.name,record.space.name)))
        return result
    
    def close_online(self):
        for record in self:
            record.write({'is_open_online': False})
            for slot in record.slots:
                slot.write({'is_open_online': False})
                