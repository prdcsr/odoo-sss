odoo.define('hms_restrict_user.stock_picking_form', function (require) {

    "use strict";

    var FormController = require('web.FormController');
    var session = require('web.session');

    FormController.include({

        renderButtons: async function () {
            this._super.apply(this, arguments);
            if (this.mode === 'readonly' && this.$buttons) {
                const disableEdit = await this.shouldDisableEdit();
                console.log(disableEdit)
                if (disableEdit) {
                    this.$buttons.find('button.o_form_button_edit').hide();  // Or use .prop('disabled', true)
                }
            }


        },

        shouldDisableEdit: async function () {
            // Example condition: based on group and a field
            const hasGroup1 = await session.user_has_group('hms_restrict_user.group_production_alsut');
            const hasGroup2 = await session.user_has_group('hms_restrict_user.group_production_gs');
            const hasGroup3 = await session.user_has_group('hms_restrict_user.group_production_btr');
            // const hasGroup3 = await session.user_has_group('stock.group_stock_user');

            const groupMatched = hasGroup1 || hasGroup2 || hasGroup3;

            // Example record condition
            const recordCondition = this.initialState && this.initialState.data.state === 'done';

            return groupMatched && recordCondition;
        }
    })


})


