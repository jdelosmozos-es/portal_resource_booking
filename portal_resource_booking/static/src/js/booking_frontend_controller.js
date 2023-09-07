odoo.define('web_appointment_by_location.appointment', function (require) {
    "use strict";

    // var Model = require('web.Model');
    var ajax = require('web.ajax');
    $(document).ready(function () {
        
        $(".container_appointment_instructions").show();
        $(".container_appointment_title").show();
        $(".container_appointment_more_info").show();
        $("#done_button").hide();
        $("#form-space-info").hide();
        $("#form-group-space").hide();
        $("#form-group-persons").hide();
        $(".container_lunch").hide();
        $(".container_dinner").hide();
        if(document.getElementById("label_max_capacity")){
            $("#label_max_capacity").html("Number of persons (Max. " + (document.getElementById("label_max_capacity").innerText ? document.getElementById("label_max_capacity").innerText : 0) + "):");
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
            a_dates.push(available_dates[span]['innerText'])
        }
        var lang = this.lastChild.lang.split('-')[0];
        $('.date_time_set_customer_calendar').datepicker({
            minDate: moment().calendar(),
            lenguage: lang,
            startView: 0,
            weekStart: 1,
            dateFormat: 'yy-mm-dd',
            icon: {
                next: 'glyphicon glyphicon-chevron-right',
                previous: 'glyphicon glyphicon-chevron-left'
            },
            availableDates: a_dates
        })
            .on('changeDate', function (e) {
                var dataFlag = false;
                var date = $(this).datepicker('getDate');
                var day = e.date.getDate();
                var month = e.date.getMonth() + 1;
                var year = e.date.getFullYear();
                var selectedDate = day + '-' + month + '-' + year;
                var space_id = 0;
                var spaceName = "";
                var instructions = "";
                $("#done_button").hide();
                $(".container_lunch").hide();
                $(".container_dinner").hide();
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
                $(".select_space_appointment").click(function () {
                    $("#step2").addClass("step-done");
                    $("#step2").removeClass("step_focus");
                    $("#step3").removeClass("step-done");
                    $("#step3").addClass("step_focus");
                    $("#step4").removeClass("step-done");
                    $("#done_button").hide();
                    $(".container_lunch").hide();
                    $(".container_dinner").hide();
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
                    $("#label_max_capacity").html("Number of persons (Max. " + numPersons + "):");
                    document.getElementById("num_persons_input").placeholder = "Max. " + numPersons;
                    $("#form-group-persons").show();
                    if (nPersons > numPersons || nPersons === false) {
                        document.getElementById("label_max_capacity").setAttribute("style", "color: #cb2e2e; transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
                    } else if (ddata === selectedDate || dataFlag !== false) {
                        $("#spinner-border-f").show();
                        ajax.jsonRpc('/calendar/timeslots', 'call', {
                            selectedDate: ddata,
                            num_persons: nPersons,
                            space_id: space_id,
                        }).then(function (event_list) {
                            $(".container_lunch").show();
                            $(".container_dinner").show();
                            $(".form-space-info").show();
                            var HTML = '';
                            var HTML2 = '';
                            for (var i in event_list['slots']) {
                                if (event_list['slots'][i] < "18:00") {
                                    HTML += '<span class="js-time-slot" id="js_slot">' + event_list['slots'][i] + '</span>';
                                } else {
                                    HTML2 += '<span class="js-time-slot" id="js_slot">' + event_list['slots'][i] + '</span>';
                                }
                            }
                            if (HTML === '') {
                                HTML += '<p>Lunch service closed</p>'
                            }
                            if (HTML2 === '') {
                                HTML2 += '<p>Dinner service closed</p>'
                            }
                            $("#spinner-border-f").hide();
                            $("#time_lunch").html(HTML);
                            $("#time_dinner").html(HTML2);
                            $('.datepicker.datepicker-dropdown.dropdown-menu').remove();
                            $("#time .js-time-slot").click(function () {
                                $("#time .js-time-slot").removeClass("js-time-slot selected");
                                $(this).addClass('js-time-slot selected');
                                $("#done_button").show();
                                $("#selectedTime1").text($(this).text());
                                $("#selectedDate1").text(ddata);
                                $("#selectedTime").val($(this).text());
                                $("#selectedDate").val(ddata);
                                var fcSelectedDate = ddata;
                                var fcSelectedTime = $(this).text();
                                $("#done_button").click(function () {
                                    $("#step3").addClass("step-done");
                                    $("#step3").removeClass("step_focus");
                                    $("#step4").removeClass("step-done");
                                    $("#step4").addClass("step_focus");
                                    var instructionImg = "";
                                    var instructionsText = "";
                                    for (var j in event_list['instructions']){
                                        if (event_list['instructions'][j]['hour'] === 0){
                                            instructionImg = event_list['instructions'][j]['img'];
                                            instructionsText = event_list['instructions'][j]['text'];
                                        }else if (event_list['instructions'][j]['hour'] === selectedTime){
                                            instructionImg = event_list['instructions'][j]['img'];
                                            instructionsText = jevent_list['instructions'][j]['test'];
                                        }
                                    }
                                    $("#form-space-info").addClass('appointment_confirm_close');
                                    $("#date_time_set_customer_calendar").addClass('appointment_confirm_close'); 
                                    $(".container_lunch").hide();
                                    $(".container_dinner").hide();
                                    $(".wrapform").addClass('appointment_confirm_open');
                                    $("#done_button").hide();
                                    $(".container_appointment_instructions").hide();
                                    $(".container_appointment_title").hide();
                                    $(".container_appointment_more_info").hide();
                                    $("#ins_img").show();   
                                    $("#ins_contact").show();
                                    $("#ins_last").show();
                                    $("#appointment_date_info").html('Booking in : ' + spaceName + " on " + fcSelectedDate + " at " + fcSelectedTime + " for " + nPersons + " persons");
                                    $("#instructions_f").val(instructionsText)
                                    if(instructionImg){
                                        $("#ins_img").html(
                                            '<h3>ADDITIONAL INFORMATION</h3>'+
                                            '<img class="card-img-top h-100" src="'+instructionImg+'" />'
                                        )
                                    }
                                    $("#appointment_done").click(function (){                                        
                                        document.getElementById("terms_conditions_label").setAttribute("style", "transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
                                        document.getElementById("emailFinal_label").setAttribute("style", "transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
                                        document.getElementById("nameFinal_label").setAttribute("style", "transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
                                        document.getElementById("phoneFinal_label").setAttribute("style", "transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
                                        var emailF = document.getElementById("emailFinal").value ? document.getElementById("emailFinal").value : false;
                                        var nameF = document.getElementById("nameFinal").value ? document.getElementById("nameFinal").value : false;
                                        var phoneF = document.getElementById("phoneFinal").value ? document.getElementById("phoneFinal").value : false;
                                        var requestF = [];
                                        for(var option of document.getElementById("appointment_requests_f").options){
                                            if(option.selected){
                                                requestF.push(option.value)
                                            }
                                        }
                                        var requestSpecialF = document.getElementById("appointment_special_requests_f").value;
                                        var instructionsF = document.getElementById("instructions_f").value;
                                        var terms = document.getElementById("terms_conditions").value ? document.getElementById("terms_conditions").value : false;

                                        if (emailF !== false && nameF !== false && phoneF !== false && terms !== false){
                                            $("#step4").addClass("step-done");
                                            $("#step4").removeClass("step_focus");
                                            var values = {
                                                name: nameF,
                                                email: emailF,
                                                phone: phoneF,
                                                request: requestF,
                                                special_request: requestSpecialF,
                                                instructions: instructionsF,
                                                start_datetime: year + '-' + month + '-' + day + ' ' + fcSelectedTime +':00',
                                                space_id: space_id,
                                                num_persons: nPersons,
                                            }
                                            ajax.jsonRpc('/appointment/book/confirm', 'call', {
                                                values: values,
                                            }).then(function (event_list) {
                                                $("#wrap_thanks").show();
                                                $(".wrapform").removeClass('appointment_confirm_open');
                                                $("#stName").html(nameF);
                                                $("#stBooking").html(fcSelectedDate + ' ' + fcSelectedTime + ' in ' + spaceName)
                                            })
                                        }else{
                                            if(terms === false){
                                                document.getElementById("terms_conditions_label").setAttribute("style", "color: #cb2e2e; transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
                                            }
                                            if(emailF === false){
                                                document.getElementById("emailFinal_label").setAttribute("style", "color: #cb2e2e; transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
                                            }
                                            if(nameF === false){
                                                document.getElementById("nameFinal_label").setAttribute("style", "color: #cb2e2e; transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
                                            }
                                            if(phoneF === false){
                                                document.getElementById("phoneFinal_label").setAttribute("style", "color: #cb2e2e; transition: all cubic-bezier(0.075, 0.82, 0.165, 1) ease-in-out;");
                                            }
                                        }

                                    })
                                })
                            });

                            if (event_list.slots.length > 0) {
                                selectedDate = 0;
                            } else {
                                dataFlag = true;
                            }
                        });
                    }
                    if (selectedDate !== 0 && nPersons !== false && nPersons < numPersons) {
                        selectedDate = '';
                    }
                })

            });
    });

});
