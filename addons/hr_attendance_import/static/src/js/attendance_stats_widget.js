odoo.define('hr_attendance_import.attendance_stats_widget', function (require) {
    "use strict";

    var time = require('web.time');
    var Widget = require('web.Widget');
    var widget_registry = require('web.widget_registry');

    var AttendanceStatsWidget = Widget.extend({
        template: 'hr_attendance_import.attendance_stats',

        /**
         * @override
         * @param {Widget|null} parent
         * @param {Object} params
         */
        init: function (parent, params) {
            this._setState(params);
            this._super(parent);
        },

        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------

        /**
         * @override to fetch data before rendering.
         */
        willStart: function () {
            return Promise.all([this._super(), this._fetchAttendancesData()]);
            return Promise.all([this._super()]);
        },

        /**
         * Fetch new data if needed (according to updated fields) and re-render the widget.
         * Called by the basic renderer when the view changes.
         * @param {Object} state
         * @returns {Promise}
         */
        updateState: function (state) {
            var self = this;
            var to_await = [];
            var updatedFields = this._setState(state);

            if (_.intersection(updatedFields, ['employee', 'date_from', 'date_to', 'id']).length) {
                to_await.push(this._fetchAttendancesData());
            }
            return Promise.all(to_await).then(function () {
                self.renderElement();
            });
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Update the state
         * @param {Object} state
         * @returns {String[]} list of updated fields
         */
        _setState: function (state) {
            var updatedFields = [];
            if (state.data.employee_id.res_id !== (this.employee && this.employee.res_id)) {
                updatedFields.push('employee');
                this.employee = state.data.employee_id;
            }
            if (state.data.date_from && state.data.date_to) {
                updatedFields.push('date_from');
                updatedFields.push('date_to');
                this.date_from = state.data.date_from;
                this.date_to = state.data.date_to;
            }
            if (state.data.id){
                updatedFields.push('id');
                this.id = state.data.id
            }
            return updatedFields;
        },

        /**
         * Fetch the number of leaves, grouped by leave type, taken by ``this.employee``
         * in the year of ``this.date``.
         * The resulting data is assigned to ``this.leavesPerType``
         * @private
         * @returns {Promise}
         */
        _fetchAttendancesData: function () {
            if (!this.date_from || !this.date_to || !this.employee) {
                this.attendancePerLeave = null;
                return Promise.resolve();
            }
            var self = this;
            var date_from = this.date_from.clone().set('hour', 0).set('minute', 0).set('sec', 0);
            var date_to = this.date_to.clone().set('hour', 23).set('minute', 59).set('sec', 59);
            return this._rpc({
                model: 'hr.attendance',
                method: 'search_read',
                kwargs: {
                    domain: [['employee_id', '=', this.employee.res_id], ['check_in', '>=', date_from], ['check_out', '<=', date_to]],
//                    domain: [['employee_id', '=', this.employee.res_id], ['leave_id', '>=', self.id]],
                    fields: ['check_in', 'check_out'],
                },
            }).then(function (data) {
                self.start_date = self.date_from.format('DD/MM/YYYY')
                self.end_date = self.date_to.format('DD/MM/YYYY')
                data.map(function(d) {
                    d.check_in = moment(d.check_in).add(7, 'hours').format('DD/MM/YYYY HH:mm')
                    d.check_out = moment(d.check_out).add(7, 'hours').format('DD/MM/YYYY HH:mm')
                    return d
                })
//                self.check_in = self.check_in.add(7, 'hours')
//                self.check_out = self.check_out.add(7, 'hours')
                self.attendancePerLeave = data;
            }).catch(function(err) {
                console.log(err)
            });
        }
    });

    widget_registry.add('attendance_stats', AttendanceStatsWidget);

    return AttendanceStatsWidget;
});
