odoo.define('booking.today_patch', function (require) {
	"use strict";

	var DateWidget = require('web.datepicker').DateWidget;
	
	DateWidget.include({
	
		init: function(parent, options) {
		
			if (options.disable_past_date) {
				var min_date = new Date()
				min_date.setHours(0)
				min_date.setMinutes(0)
				options.minDate = moment(min_date);
//				options.beforeShowDay = function(date) {
//							console.log(date);
//							return [true,""]
//						}
			}
			this._super.apply(this, arguments);
		},

	
	});
});