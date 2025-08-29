odoo.define('transfer_product_category_qty.category_summary_widget', function (require) {
    "use strict";

    var time = require('web.time');
    var Widget = require('web.Widget');
    var widget_registry = require('web.widget_registry');

    var CategorySummaryWidget = Widget.extend({
        template: 'transfer_product_category_qty.category_summary',

        init: function (parent, params) {
            this._setState(params);
            this._super(parent);
        },

        willStart: function () {
            return Promise.all([this._super(), this._fetchCurrentProductCategory()]);
        },

        updateState: function (state) {
            var self = this;
            var to_await = [];
            var updatedFields = this._setState(state);

//            if (_.intersection(updatedFields, ['employee', 'date']).length) {
//                to_await.push(this._fetchLeaveTypesData());
//            }
            if (_.intersection(updatedFields, ['move_lines']).length) {
                to_await.push(this._fetchCurrentProductCategory());
            }
            return Promise.all(to_await).then(function () {
                self.renderElement();
            });
        },

        _setState: function (state) {
            var updatedFields = [];
            if (state.data.move_ids_without_package && state.data.move_ids_without_package.data){
                updatedFields.push('move_lines');
                this.stock_moves = state.data.move_ids_without_package.data
            }
            if (state.data.picking_type_id && state.data.picking_type_id.data){
                this.picking_type = state.data.picking_type_id.data
            }
//            if (state.data.employee_id.res_id !== (this.employee && this.employee.res_id)) {
//                updatedFields.push('employee');
//                this.employee = state.data.employee_id;
//            }
//            if (state.data.date_from !== this.date) {
//                updatedFields.push('date');
//                this.date = state.data.date_from;
//            }
            return updatedFields;
        },

        _fetchCurrentProductCategory: function () {
            var self = this;
            const summary = {};
            if (self.stock_moves){

                self.stock_moves.forEach(move => {
                    const product_category = move.data.product_categ_id;
                    const qty = move.data.product_uom_qty;

                    if (product_category) {
                        const categoryName = product_category.data.display_name;
                        summary[categoryName] = (summary[categoryName] || 0) + qty;
                    }
                });
            }

            if (_.isEmpty(summary)){
                self.categorySummary = null
            }
            else{
                self.categorySummary = Object.entries(summary) || []
            }


//            if (this.employee){
//                return this._rpc({
//                    model: 'hr.leave',
//                    method: 'read_group',
//                    kwargs: {
//                        domain: [['employee_id', '=', this.employee.res_id], ['state', '=', 'validate'], ['date_from', '>=', year_date_from], ['date_to', '<=', year_date_to]],
//                        fields: ['holiday_status_id', 'number_of_days:sum'],
//                        groupby: ['holiday_status_id'],
//                    },
//                }).then(function (data) {
//                    self.leaveSummary = data;
//                });
//            }
            return summary

        }
    })

    widget_registry.add('category_summary', CategorySummaryWidget);

    return CategorySummaryWidget;
})