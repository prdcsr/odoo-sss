odoo.define('tis_sales_dashboard.sales_dashboard', function (require) {
'use strict';

var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var Dialog = require('web.Dialog');
var field_utils = require('web.field_utils');
var session = require('web.session');
var time = require('web.time');
var web_client = require('web.web_client');
var framework = require('web.framework');
var ActionManager = require('web.ActionManager');
var view_registry = require('web.view_registry');
var Widget = require('web.Widget');
//var ControlPanelMixin = require('web.ControlPanelMixin');

var _t = core._t;
var _lt = core._lt;
var QWeb = core.qweb;
var SalesDashboard = AbstractAction.extend({
hasControlPanel: false,

	events: {
	},
	init: function(parent, context) {
        this._super(parent, context);
        var sale_data = [];
        var self = this;
        if (context.tag == 'sale_dashboard') {
            self._rpc({
                model: 'sales.dashboard',
                method: 'get_sale_info',
            }, []).then(function(result){
                self.sale_data = result
            }).then(function(){
                self.render();
                self.href = window.location.href;
            });
        }
    },
    willStart: function() {
         return $.when(ajax.loadLibs(this), this._super());
    },
    start: function() {
        var self = this;
        return this._super();
    },
    render: function() {
        var super_render = this._super;
        var self = this;
        var sales_dashboard = QWeb.render( 'SaleDashboarddata', {
            widget: self,
        });
        $( ".o_control_panel" ).addClass( "o_hidden" );
        $(sales_dashboard).prependTo(self.$el);
     self.graph();
        return sales_dashboard
    },
    reload: function () {
            window.location.href = this.href;
    },

//     Function which gives random color for charts.
    getRandomColor: function () {
        var letters = '0123456789ABCDEF'.split('');
        var color = '#';
        for (var i = 0; i < 6; i++ ) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    },

//     Here we are plotting bar,pie chart
  graph: function() {
        var self = this
//        var ctx = this.$el.find('#salebarChart')
//         Fills the canvas with white background
        Chart.plugins.register({
          beforeDraw: function(chartInstance) {
            var ctx = chartInstance.chart.ctx;
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, chartInstance.chart.width, chartInstance.chart.height);
          }
        });
        var bg_color_list = []
        for (var i=0;i<=11;i++){
            bg_color_list.push(self.getRandomColor())
        }
          var ctx = this.$el.find('#barChartDemo')
       var salesChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: self.sale_data[14],
                datasets: [{
                    label: 'Sales by Month',
                    data: self.sale_data[15],
                    backgroundColor: bg_color_list,
                    borderColor: bg_color_list,
                    borderWidth: 1,
                    pointBorderColor: 'white',
                    pointBackgroundColor: 'red',
                    pointRadius: 5,
                    pointHoverRadius: 10,
                    pointHitRadius: 30,
                    pointBorderWidth: 2,
                    pointStyle: 'rectRounded'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                animation: {
                    duration: 100, // general animation time
                },
                hover: {
                    animationDuration: 500, // duration of animations when hovering an item
                },
                responsiveAnimationDuration: 500, // animation duration after a resize
                legend: {
                    display: true,
                    labels: {
                        fontColor: 'black'
                    }
                },
            },
        });

  var piectx1 = this.$el.find('#doughnutChartDemo');
        bg_color_list = []
        for (var i=0;i<=self.sale_data[11].length;i++){
            bg_color_list.push(self.getRandomColor())
        }
        var doughnutChart = new Chart(piectx1, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: self.sale_data[11],
                    backgroundColor: bg_color_list,
                    label: 'Payment Methods'
                }],
                labels:self.sale_data[10],
            },
            options: {
                responsive: true
            }
        });
        var piectx3 = this.$el.find('#doughnutChartDemo1');
        bg_color_list = []
        for (var i=0;i<=self.sale_data[13].length;i++){
            bg_color_list.push(self.getRandomColor())
        }
        var doughnutChart = new Chart(piectx3, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: self.sale_data[13],
                    backgroundColor: bg_color_list,
                    label: 'Payment Methods'
                }],
                labels:self.sale_data[12],
            },
            options: {
                responsive: true
            }
        });

/*
 */      /* Pie Chart*/
        var piectx = this.$el.find('#pieChartDemo');
        bg_color_list = []
        for (var i=0;i<=self.sale_data[9].length;i++){
            bg_color_list.push(self.getRandomColor())
        }
//        piectx.fillText('20000' + "%", 20/2 - 20, 20/2, 200);
        var pieChart = new Chart(piectx, {
            type: 'pie',
            data: {
                datasets: [{
                    data: self.sale_data[9],
                    backgroundColor: bg_color_list,
                    label: 'Top 5 Category'
                }],
                labels:self.sale_data[8],
            },
            options: {
                responsive: true
            }
        });

    },

});
core.action_registry.add('sale_dashboard', SalesDashboard);
return SalesDashboard
});