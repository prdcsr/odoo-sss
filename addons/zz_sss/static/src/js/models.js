
// @author: Hidayat Khouw
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

odoo.define("pos_margin.models", function(require) {
    "use strict";

    var models = require("point_of_sale.models"); 

    

    // /////////////////////////////
    // Overload models.export.orderline
    // /////////////////////////////
    var OrderLineMargin = models.Orderline.extend({
       
        export_as_JSON: function() {
            
            get_unit_price_default: function(){
                var unitprice = this.product.get_price(this.pos.post_pricelist, this.get_quantity());
                return unitprice;
            },

        ]
    });

    models.Orderline = OrderLineMargin;
});
