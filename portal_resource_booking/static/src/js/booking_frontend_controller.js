odoo.define('portal_resource_booking.booking', function (require) {
	"use strict";

	var PublicWidget = require('web.public.widget');
	// var Model = require('web.Model');
	var ajax = require('web.ajax');
	var time = require('web.time');
	var core = require('web.core');
	var _t = core._t;
	var NewData = PublicWidget.Widget.extend({
		selector: '#date_time_set_customer_calendar',
		start: function () {
			$(".container_appointment_instructions").show();
			$(".container_appointment_title").show();
			$(".container_appointment_more_info").show();
			$("#done_button").hide();
			$("#form-space-info").hide();
			$("#form-group-space").hide();
			$("#form-group-persons").hide();
			$("#time").hide();
			if (document.getElementById("label_max_capacity")) {
				$("#label_max_capacity").html(_t("Number of persons")) // (Max. " + (document.getElementById("label_max_capacity").innerText ? document.getElementById("label_max_capacity").innerText : 0) + "):");
			}
			$("#step1").addClass("step_focus");
			$("#step2").removeClass("step-done");
			$("#step3").removeClass("step-done");
			$("#step4").removeClass("step-done");
			var cards = $(".card-body");
			for (var card = 0; card < cards.length; card++) {
				cards[card].setAttribute("style", "transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
			}
			var available_dates = $('.available_dates');
			var a_dates = []
			for (var span = 0; span < available_dates.length; span++) {
				a_dates.push(JSON.parse(available_dates[span]['innerText'])) //.split('/').map(Number))
			}
			var currentText = "Today"; // Display text for current month link
			var monthNames = [ "January","February","March","April","May","June",
				"July","August","September","October","November","December" ];// Names of months for drop-down and formatting
			var monthNamesShort = [ "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" ]; // For formatting
			var dayNames = [ "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday" ]; // For formatting
			var dayNamesShort = [ "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" ]; // For formatting
			var dayNamesMin = [ "Su","Mo","Tu","We","Th","Fr","Sa" ]; // Column headings for days starting at Sunday
			var weekHeader = "Wk"; // Column header for week of the year
			var dateFormat =  "mm/dd/yy";
			var firstDay = 0;
			if(moment.locale() === 'es'){
				currentText = "Hoy";
				monthNames = [ "Enero","Febrero","Marzo","Abril","Mayo","Junio",
				"Julio","Agosto","Septiembre","Octubre","Noviember","Diciembre" ];
				monthNamesShort = [ "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dec" ];
				dayNames = [ "Domingo", "Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado" ];
				dayNamesShort = [ "Dom", "Lun", "Mar", "Mie", "Jue", "Vie", "Sab" ]; 
				dayNamesMin = [ "Do","Lu","Ma","Mi","Ju","Vi","Sa" ];
				weekHeader = "Sm";
				dateFormat =  "dd/mm/yy";
				firstDay = 1;
			}
			if(moment.locale() === 'ca'){
				currentText = "Avui";
				monthNames = [ "Gener","Febrer","Març","Abril","Maig","Juny",
				"Juliol","Agost","Setembre","Octubre","Novembre","Desembre" ];
				monthNamesShort = [ "Gen", "Febr", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Des" ];
				dayNames = [ "Diumenge", "Dilluns", "Dimarts", "Dimecres", "Dijous", "Divendres", "Dissabet" ];
				dayNamesShort = [ "Dg", "Dl", "Dt", "Dc", "Dj", "Dv", "Ds" ]; 
				dayNamesMin = [ "Dg", "Dl", "Dt", "Dc", "Dj", "Dv", "Ds" ];
				weekHeader = "Sm";
				dateFormat =  "dd/mm/yy";
				firstDay = 1;
			}
			$('.date_time_set_customer_calendar').datepicker({  
				currentText: currentText,
				monthNames: monthNames,
				monthNamesShort: monthNamesShort,
				dayNames: dayNames,
				dayNamesShort: dayNamesShort,
				dayNamesMin: dayNamesMin,
				weekHeader: weekHeader,
				dateFormat: dateFormat,
				firstDay: firstDay,
				//            startView: 0,
				//            weekStart: 1,
				//            dateFormat: 'yy-mm-dd',
				//            format: time.getLangDatetimeFormat(),

				//            availableDates: a_dates,
				//        })
				//            .on('Select', function (e) {
				beforeShowDay: function (date) {
					var day = date.getDate();
					var month = date.getMonth() + 1;
					var year = date.getFullYear();
					let i = 0;
					let selectable = false;
					while (i < a_dates.length) {
						if (day == a_dates[i].day && month == a_dates[i].month && year == a_dates[i].year) {
							selectable = true;
							break
						}
						i++
					}
					return [selectable, ""]
				},
				onSelect: function (e) {
					var dataFlag = false;
					//                var date = $(this).datepicker('getDate');
					self = jQuery.datepicker._getInst($('#date_time_set_customer_calendar')[0])
					//                var day = e.date.getDate();
					var day = self.selectedDay
					//                var month = e.date.getMonth() + 1;
					var month = self.selectedMonth + 1
					//                var year = e.date.getFullYear();
					var year = self.selectedYear
					var selectedDate = day + '-' + month + '-' + year;
					var space_id = 0;
					var spaceName = "";
					var instructions = "";
					$("#done_button").hide();
					$("#time").hide();
					$("#form-space-info").hide();
					$("#form-space-info").show();
					$("#form-group-persons").show();
					$("#selectedTime1").text('');
					$("#selectedDate1").text(selectedDate);
					document.getElementById("label_max_capacity").setAttribute("style", "transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
					$("#step1").addClass("step-done");
					$("#step1").removeClass("step_focus");
					$("#step2").removeClass("step-done");
					$("#step2").addClass("step_focus");
					$("#step3").removeClass("step-done");
					$("#step4").removeClass("step-done");
					var ddata = selectedDate;
					$(".select_space_appointment").on( "click",function () {
						$("#step2").addClass("step-done");
						$("#step2").removeClass("step_focus");
						$("#step3").removeClass("step-done");
						$("#step3").addClass("step_focus");
						$("#step4").removeClass("step-done");
						$("#done_button").hide();
						$(".container_lunch").hide(); //FIXME: estos deben ser types
						$(".container_dinner").hide(); //FIXME: estos deben ser types
						document.getElementById("space_id").value = this.attributes.name.value
						spaceName = this.attributes.opt.value
						var cards = $(".card-body");
						for (var card = 0; card < cards.length; card++) {
							cards[card].setAttribute("style", "transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
						}
						this.parentNode.closest(".card-body").setAttribute("style", "background: rgb(29, 231, 0, 0.34) !important;transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
						document.getElementById("label_max_capacity").setAttribute("style", "transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
						space_id = this.attributes.name.value;
						var numPersons = this.attributes.nodevalue.value;
						var num = document.getElementById("num_persons_input").value | 0;
						var nPersons = num > 0 ? num : false;
						$("#label_max_capacity").html(_t("Number of persons")); // (Max. " + numPersons + "):");
						//document.getElementById("num_persons_input").placeholder = "Max. " + numPersons;
						$("#form-group-persons").show();
						if (nPersons > numPersons || nPersons === false) {
							document.getElementById("label_max_capacity").setAttribute("style", "color: #cb2e2e; transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
							dataFlag = true;
						} else if (ddata === selectedDate || dataFlag !== false) {
							$("#spinner-border-f").show();
							ajax.jsonRpc('/calendar/timeslots', 'call', {
								selectedDate: ddata,
								num_persons: nPersons,
								space_id: space_id,
							}).then(function (event_list) {
								$("#time").show();
								$(".form-space-info").show();
								console.log(event_list);
								var HTML2 = '';
								for (var type in event_list['types'] ){
									var HTML = '<div class="type_service"><h4 style="text-align: center; color: rgb(1, 84, 71);">'+event_list['types'][type] +'</h4><div>';
									var fl = false
									for (var i in event_list['slots']) {
										
										if (event_list['slots'][i]['type'] === event_list['types'][type]){
											HTML += '<span class="js-time-slot" id="js_slot">' + event_list['slots'][i]['value'] + '</span>';
											fl = true
										}
									}
									if(fl === false){
										HTML += '<p style="text-align: center; color: rgb(1, 84, 71);">Closed service</p>'
									}
									HTML += '</div></div>';
									HTML2 += HTML;
								}
								if(HTML2 === ''){
									HTML2 += '<p style="text-align: center; color: rgb(1, 84, 71);">There are no avaiable slots</p>'
								}
								$("#spinner-border-f").hide();
								$("#time").html(HTML2);
								$('.datepicker.datepicker-dropdown.dropdown-menu').remove();
								$("#time .js-time-slot").on( "click",function () {
									$("#time .js-time-slot").removeClass("js-time-slot selected");
									$(this).addClass('js-time-slot selected');
									$("#done_button").show();
									$("#selectedTime1").text($(this).text());
									$("#selectedDate1").text(ddata);
									$("#selectedTime").val($(this).text());
									$("#selectedDate").val(ddata);
									var fcSelectedDate = ddata;
									var fcSelectedTime = $(this).text();
									$("#done_button").on( "click",function () {
										$("#step3").addClass("step-done");
										$("#step3").removeClass("step_focus");
										$("#step4").removeClass("step-done");
										$("#step4").addClass("step_focus");
										var instructionImg = "";
										var instructionsText = "";
										for (var j in event_list['instructions']) {
											if (event_list['instructions'][j]['hour'] === 0) {
												instructionImg = event_list['instructions'][j]['img'];
												instructionsText = event_list['instructions'][j]['text'];
											} else if (event_list['instructions'][j]['hour'] === selectedTime) {
												instructionImg = event_list['instructions'][j]['img'];
												instructionsText = jevent_list['instructions'][j]['test'];
											}
										}
										$("#form-space-info").addClass('appointment_confirm_close');
										$("#date_time_set_customer_calendar").addClass('appointment_confirm_close');
										$("#time").hide();
										$(".ui-datepicker").hide();
										$(".wrapform").addClass('appointment_confirm_open');
										$("#done_button").hide();
										$(".container_appointment_instructions").hide();
										$(".container_appointment_title").hide();
										$(".container_appointment_more_info").hide();
										$("#ins_img").show();
										$("#ins_contact").show();
										$("#ins_last").show();
										$("#appointment_date_info").html(_t('Booking in : ') + spaceName + _t(" on ") + fcSelectedDate + _t(" at ") + fcSelectedTime + _t(" for ") + nPersons + _t(" persons"));
										$("#instructions_f").val(instructionsText)
										if (instructionImg) {
											$("#ins_img").html(
												'<h3>ADDITIONAL INFORMATION</h3>' +
												'<img class="card-img-top h-100" src="' + instructionImg + '" />'
											)
										}
										$("#appointment_done").on( "click",function () {
											document.getElementById("terms_conditions_label").setAttribute("style", "transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
											document.getElementById("emailFinal_label").setAttribute("style", "transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
											document.getElementById("nameFinal_label").setAttribute("style", "transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
											document.getElementById("phoneFinal_label").setAttribute("style", "transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
											var emailF = document.getElementById("emailFinal").value ? document.getElementById("emailFinal").value : false;
											var nameF = document.getElementById("nameFinal").value ? document.getElementById("nameFinal").value : false;
											var phoneF = document.getElementById("phoneFinal").value ? document.getElementById("phoneFinal").value : false;
											var requestF = [];
											for (var option of document.getElementById("appointment_requests_f").options) {
												if (option.selected) {
													requestF.push(option.value)
												}
											}
											var requestSpecialF = document.getElementById("appointment_special_requests_f").value;
											var instructionsF = document.getElementById("instructions_f").value;
											var terms = $("#terms_conditions")[0].checked //document.getElementById("terms_conditions").value ? document.getElementById("terms_conditions").value : false;

											if (emailF !== false && nameF !== false && phoneF !== false && terms !== false) {
												$("#step4").addClass("step-done");
												$("#step4").removeClass("step_focus");
												var values = {
													name: nameF,
													email: emailF,
													phone: phoneF,
													request: requestF,
													special_request: requestSpecialF,
													instructions: instructionsF,
													//	                                                start_datetime: year + '-' + month + '-' + day + ' ' + fcSelectedTime +':00',
													date: { 'year': year, 'month': month, 'day': day },
													time_string: fcSelectedTime,
													space_id: space_id,
													num_persons: nPersons,
												}
												ajax.jsonRpc('/appointment/book/confirm', 'call', {
													values: values,
												}).then(function (response) {
													$(".wrapform").removeClass('appointment_confirm_open');
													$("#stName").html(nameF);
													if ('error' in response) {
														$("#stBooking").html('Error: '+response.error)
													} else {
														$("#stBooking").html(fcSelectedDate + ' ' + fcSelectedTime + ' in ' + spaceName)
													}
													$("#wrap_thanks").show();
												})
											} else {
												if (terms === false) {
													document.getElementById("terms_conditions_label").setAttribute("style", "color: #cb2e2e; transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
												}
												if (emailF === false) {
													document.getElementById("emailFinal_label").setAttribute("style", "color: #cb2e2e; transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
												}
												if (nameF === false) {
													document.getElementById("nameFinal_label").setAttribute("style", "color: #cb2e2e; transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
												}
												if (phoneF === false) {
													document.getElementById("phoneFinal_label").setAttribute("style", "color: #cb2e2e; transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
												}
											}

										})
									})
								});

								if (event_list.slots.length > 0) {
									selectedDate = 0;
									dataFlag = true;
								} else {
									dataFlag = true;
								}
							});
						}
						if (selectedDate !== 0 && nPersons !== false && nPersons < numPersons) {
							selectedDate = '';
						}
					})
				}
			});
			//			MyDatePicker.locale(document.querySelector("html").getAttribute("lang"))
		},
	});
	PublicWidget.registry.Booking = NewData;
	return NewData;
});