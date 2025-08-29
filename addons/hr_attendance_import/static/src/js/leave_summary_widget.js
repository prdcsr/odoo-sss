odoo.define('hr_attendance_import.leave_summary_widget', function (require) {
    "use strict";

    var time = require('web.time');
    var Widget = require('web.Widget');
    var widget_registry = require('web.widget_registry');

    var LeaveStatsWidget = Widget.extend({
        template: 'hr_attendance_import.leave_summary',

        init: function (parent, params) {
            this._setState(params);
            this._super(parent);
        },

        willStart: function () {
            return Promise.all([this._super(), this._fetchLeaveTypesData(), this._fetchLeavesDate()]);
        },

        updateState: function (state) {
            var self = this;
            var to_await = [];
            var updatedFields = this._setState(state);

            if (_.intersection(updatedFields, ['employee', 'date']).length) {
                to_await.push(this._fetchLeaveTypesData());
            }
            if (_.intersection(updatedFields, ['date']).length) {
                to_await.push(this._fetchLeavesDate());
            }
            return Promise.all(to_await).then(function () {
                self.renderElement();
            });
        },

        _setState: function (state) {
            var updatedFields = [];
            if (state.data.employee_id.res_id !== (this.employee && this.employee.res_id)) {
                updatedFields.push('employee');
                this.employee = state.data.employee_id;
            }
            if (state.data.date_from !== this.date) {
                updatedFields.push('date');
                this.date = state.data.date_from;
            }
            return updatedFields;
        },

        _fetchLeavesDate: function () {
            if (!this.date) {
                this.departmentLeaves = null;
                return Promise.resolve();
            }
            var self = this;
            var year_date_from = this.date.clone().startOf('year');
            var year_date_to = this.date.clone().endOf('year');
            if (this.employee){
                return this._rpc({
                    model: 'hr.leave',
                    method: 'search_read',
                    args: [
                        [['employee_id', '=', this.employee.res_id],
                        ['state', '=', 'validate'],
                        ['holiday_type', '=', 'employee'],
                        ['date_from', '<=', year_date_to],
                        ['date_to', '>=', year_date_from]],
                        ['employee_id', 'date_from', 'date_to', 'number_of_days', 'holiday_status_id', 'name'],
                    ],
                }).then(function (data) {
                    var dateFormat = time.getLangDateFormat();
                    self.leavesDate = data.map(function (leave) {
                        // Format datetimes to date (in the user's format)
                        return _.extend(leave, {
                            name: leave.name,
                            holiday_status_id: leave.holiday_status_id,
                            date_from: moment(leave.date_from).format('DD-MM-YYYY'),
                            date_to: moment(leave.date_to).format('DD-MM-YYYY'),
                            number_of_days: leave.number_of_days,
                        });
                    });
                });
            }
            return []
        },

        _fetchLeaveTypesData: function () {
            if (!this.date) {
                this.leavesPerType = null;
                return Promise.resolve();
            }
            var self = this;
            var year_date_from = this.date.clone().startOf('year');
            var year_date_to = this.date.clone().endOf('year');
            if (this.employee){
                return this._rpc({
                    model: 'hr.leave',
                    method: 'read_group',
                    kwargs: {
                        domain: [['employee_id', '=', this.employee.res_id], ['state', '=', 'validate'], ['date_from', '>=', year_date_from], ['date_to', '<=', year_date_to]],
                        fields: ['holiday_status_id', 'number_of_days:sum'],
                        groupby: ['holiday_status_id'],
                    },
                }).then(function (data) {
                    self.leaveSummary = data;
                });
            }
            return []

        }
    })

    widget_registry.add('hr_leave_summary', LeaveStatsWidget);

    return LeaveStatsWidget;
})