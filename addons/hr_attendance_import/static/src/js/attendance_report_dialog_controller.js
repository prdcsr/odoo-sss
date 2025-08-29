odoo.define('hr_attendance_import.AttendanceFormController', function (require) {
    "use strict";

    var core = require('web.core');
    var AttendanceFormController = require('web.FormController');
    var Dialog = require('web.Dialog');

    var qweb = core.qweb;

    AttendanceFormController.include({
        renderButtons: function($node){
            this._super.apply(this, arguments);
        },

        _onButtonClicked: function(event){
            if (event.data.attrs.id === "attendance_import_button_submit"){
                var ctx = this
                var file_input = $('#attendance_file')

                var file = file_input[0].files[0]

                if (!file){
                    Dialog.alert(this, "File excel wajib diupload")
                }
                else{
                    var formData = new FormData()
                    formData.append('file', file)

                    var request = $.ajax({
                        type: "POST",
                        url: "/hr_attendance/import",
                        enctype: 'multipart/form-data',
                        data: formData,
                        processData: false,
                        contentType: false
                    });

                    request.done(function(response){
                         ctx.do_action({
                            'type': 'ir.actions.act_window_close'
                         })
                         ctx.do_action({
                            name: 'Attendances',
                            res_model: 'hr.attendance',
                            views: [[false, 'list'], [false, 'kanban']],
                            type: 'ir.actions.act_window',
                            view_mode: 'tree'
                         })
                    })

                    request.fail(function(jqXHR, textStatus, errorThrown){
                        Dialog.alert(this, "The following error occurred: " + errorThrown)
                    })
                }
            }

            if (event.data.attrs.id === "attendance_import_button_submit_solution"){
                var ctx = this
                var file_input = $('#attendance_file_solution')

                var file = file_input[0].files[0]

                if (!file){
                    Dialog.alert(this, "File excel wajib diupload")
                }
                else{
                    var formData = new FormData()
                    formData.append('file', file)

                    var request = $.ajax({
                        type: "POST",
                        url: "/hr_attendance/import/solution",
                        enctype: 'multipart/form-data',
                        data: formData,
                        processData: false,
                        contentType: false
                    });

                    request.done(function(response){
                         ctx.do_action({
                            'type': 'ir.actions.act_window_close'
                         })
                         ctx.do_action({
                            name: 'Attendances',
                            res_model: 'hr.attendance',
                            views: [[false, 'list'], [false, 'kanban']],
                            type: 'ir.actions.act_window',
                            view_mode: 'tree'
                         })
                    })

                    request.fail(function(jqXHR, textStatus, errorThrown){
                        Dialog.alert(this, "The following error occurred: " + errorThrown)
                    })
                }
            }

            else if (event.data.attrs.id === "summary_export_button_submit"){
                var ctx = this
                var month = $('#month')

                if (month[0].value){
                    var day = new Date(month[0].value)
                    var start = new Date(day.getFullYear(), day.getMonth(), 1, 23, 59, 59).toISOString()
                    var end  = new Date(day.getFullYear(), day.getMonth() + 1, 0, 23, 59, 59).toISOString()

                    if (start > end){
                        Dialog.alert(this, 'Tanggal akhir wajib lebih besar dari tanggal awal')
                    }
                    else{

                        start = start.substring(0, start.indexOf('T'))
                        end = end.substring(0, end.indexOf('T'))

                        var data = new FormData()
                        data.append('start_date', start)
                        data.append('end_date', end)

                        var request = $.ajax({
                            type: "POST",
                            url: "/hr_summary/export",
                            data: data,
                            enctype: "multipart/form-data",
                            processData: false,
                            contentType: false,
                        });

                        request.done(function(data, textStatus, request){
                            var contentDisposition = request.getResponseHeader('Content-Disposition')
                            var fileName = contentDisposition.substring(contentDisposition.indexOf("'") + 2)
                            var contentType = request.getResponseHeader('Content-Type')
                            var attachmentId = request.getResponseHeader('attachment')

                            var blob = new Blob([data], {type: contentType})
                            var download_url = '/web/content/' + attachmentId + '?download=true'

                            ctx.do_action({
                                "type": "ir.actions.act_url",
	                            "url": download_url,
	                            'target': "_blank"
                            })

                        })


                        request.fail(function(jqXHR, textStatus, errorThrown){
                            Dialog.alert(this, "The following error occurred: " + errorThrown)
                        })
                    }

                }
                else{
                    Dialog.alert(this, "Tanggal awal dan akhir wajib diisi")
                }
            }

            	this._super(event);
        },

    })

})