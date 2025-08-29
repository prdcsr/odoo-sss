odoo.define('hr_attendance_import.AttendanceListController', function (require) {
    "use strict";

    var core = require('web.core');
    var ListController = require('web.ListController');

    var qweb = core.qweb;

    ListController.include({
        renderButtons: function($node){
            this._super.apply(this, arguments);
           if (this.$buttons) {
             this.$buttons.find('.attendance_import_button').click(this.proxy('_onOpenWizard')) ;
             this.$buttons.find('.attendance_import_button_solution').click(this.proxy('_onOpenWizardSolution')) ;
           }
        },

        _onOpenWizard: function () {
            var state = this.model.get(this.handle, {raw: true});
            var stateContext = state.getContext();
            var context = {
                active_model: this.modelName,
            };
            this.do_action({
                name: 'Attendance Import',
                res_model: 'attendance.import.form',
                views: [[false, 'form']],
                target: 'new',
                type: 'ir.actions.act_window',
                view_mode: 'form'
            });
        },

        _onOpenWizardSolution: function () {
            var state = this.model.get(this.handle, {raw: true});
            var stateContext = state.getContext();
            var context = {
                active_model: this.modelName,
            };
            this.do_action({
                name: 'Attendance Import',
                res_model: 'attendance.import.form.solution',
                views: [[false, 'form']],
                target: 'new',
                type: 'ir.actions.act_window',
                view_mode: 'form',
            });
        },


    })

})