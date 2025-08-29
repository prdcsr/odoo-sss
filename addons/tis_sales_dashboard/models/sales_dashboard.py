# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.
from datetime import datetime, timedelta

from odoo import models, api


class SalesDashboard(models.Model):
    _name = 'sales.dashboard'
    _description = "dashboard"

    @api.model
    def get_sale_info(self):
        cr = self.env.cr
        currency_id = self.env.user.company_id.currency_id.symbol
        company_id = self.env.user.company_id.id
        query = """
                    select count(q.state) as todays_quotations
                    from sale_order q
                    where q.state = 'draft' and q.create_date >= date_trunc('day', CURRENT_DATE) and q.create_date < CURRENT_DATE+1 and q.company_id = %s

                    """ % (company_id)
        cr.execute(query)
        todays_quotation = cr.dictfetchall()

        query = """
                            select count(q.state) as quotations_this_month
                            from sale_order q
                            where q.state = 'draft' and q.create_date >= date_trunc('month', CURRENT_DATE) and q.create_date < DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month')  and q.company_id = %s

                            """ % (company_id)
        cr.execute(query)
        quotations_this_month = cr.dictfetchall()

        query = """
                            select count(q.state) as todays_sale_orders
                            from sale_order q
                            where q.state = 'sale' and q.create_date >= date_trunc('day', CURRENT_DATE) and q.create_date < CURRENT_DATE+1 and q.company_id = %s

                            """ % company_id
        cr.execute(query)
        todays_sale_orders = cr.dictfetchall()

        query = """
                                    select count(q.state) as sale_orders_this_month
                                    from sale_order q
                                    where q.state = 'sale' and q.create_date >= date_trunc('month', CURRENT_DATE) and q.create_date < DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month') and q.company_id = %s

                                    """ % company_id
        cr.execute(query)
        sale_orders_this_month = cr.dictfetchall()

        query = """
                                    select sum(q.amount_untaxed) as total_amount_this_year
                                    from sale_order q
                                    where (state = 'sale' or state = 'done' )and extract(year from q.date_order) = extract(year from CURRENT_DATE) 
                                    and not q.partner_id = any(array[5699,5878]) and q.company_id = %s

                                    """ % company_id 
        cr.execute(query)
        to_be_invoiced = cr.dictfetchall()

        query = """
                                    select sum(q.amount_untaxed) as total_amount_invoiced
                                    from sale_order q
                                    where q.state = any(array['sale','done']) and date(q.date_order) = CURRENT_DATE 
                                    and not q.partner_id = any(array[5699,5878]) and q.company_id = %s

                                    """ % company_id
       
        #query = """
        #                            select sum(aml.price_total) as total_amount_invoiced
        #                            from sale_order_line sl
         #                           left join sale_order_line_invoice_rel rel on (sl.id = rel.order_line_id)
         #                           left join account_move_line aml on (aml.id = rel.invoice_line_id)
         #                           where sl.create_date >= date_trunc('month', CURRENT_DATE) and sl.create_date < DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month') and sl.company_id = %s
         #                           """ % company_id
        cr.execute(query)
        total_amount_invoiced_this_month = cr.dictfetchall()

        query = """
                                    select sum(q.amount_untaxed) as amount_total_this_month
                                    from sale_order q
                                    where (state = 'sale' or state = 'done' ) and 
                                    q.date_order >= date_trunc('month', CURRENT_DATE) and q.date_order < DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month') 
                                    and not q.partner_id = any(array[5699,5878]) and q.company_id = %s

                                    """ % company_id
        cr.execute(query)
        amount_total_this_month = cr.dictfetchall()
        #s_total_this_month = amount_total_this_month[0]['amount_total_this_month']
        #amount_total_this_month[0]['amount_total_this_month'] = round(s_total_this_month/1000000,0)

        query = """
                            select s.partner_id, sum(s.amount_untaxed) as total
                            from sale_order s
                            where s.date_order >= date_trunc('month', CURRENT_DATE) and s.date_order < DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month') 
                            and not s.partner_id = any(array[5699,5878]) and s.company_id = %s
                            group by s.partner_id
                            order by total DESC limit 5
                                    """ % company_id
        cr.execute(query)
        top5_customers = cr.dictfetchall()
        datas = []
        totals = []
        for data in top5_customers:
            partner = self.env['res.partner'].browse(data['partner_id'])
            datas.append(partner.name)

            totals.append(data['total'])

        query = """
                        select t.default_code as name, sum(price_subtotal) as count
                        from product_template t
                        inner join product_product p
                        on t.id = p.product_tmpl_id
                        inner join sale_order_line s
                        on s.product_id = p.id left outer join sale_order q on s.order_id=q.id
                        where s.create_date >= date_trunc('month', CURRENT_DATE) and s.create_date < DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month') 
                        and not q.partner_id = any(array[5699,5878]) and s.company_id = %s and t.type='product'
                        group by t.default_code
                        order by count DESC limit 5

                                            """ % company_id
        cr.execute(query)
        top5_products = cr.dictfetchall()
        product_name = []
        product_count = []
        for data in top5_products:
            product_name.append(data['name'])
            product_count.append(data['count'])

        query = """
                        select t.user_id, sum(t.amount_untaxed) as total
                        from sale_order t
                        where (state = 'sale' or state = 'done') and t.create_date >= date_trunc('month', CURRENT_DATE) and t.create_date < DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month') 
                        and not t.partner_id = any(array[5699,5878]) and t.company_id = %s
                        group by t.user_id
                        order by total DESC limit 5 
                        """ % company_id
        cr.execute(query)
        top5_sales_team = cr.dictfetchall()
        team_name = []
        team_count = []
        for data in top5_sales_team:
            sales_team = self.env['res.users'].browse(data['user_id'])
            team_name.append(sales_team.name)
            team_count.append(data['total'])

        query = """
                                select extract(month from s.date_order) as month,to_char(s.date_order,'Mon')as sale_month, sum(s.amount_untaxed) as total
                                from sale_order s
                                where (s.state = 'sale' or s.state = 'done') and extract(year from s.date_order)  = extract(year from CURRENT_DATE)  
                                and not s.partner_id = any(array[5699,5878]) and s.company_id = %s
                                group by month, sale_month order by month
                                """ % company_id
        cr.execute(query)
        sales_by_month = cr.dictfetchall()
        month = []
        sale = []
        for data in sales_by_month:
            month.append(data['sale_month'])
            sale.append(data['total'])

        return todays_quotation[0], quotations_this_month[0], todays_sale_orders[0], \
               sale_orders_this_month[0], to_be_invoiced[0], amount_total_this_month[0], \
               currency_id, total_amount_invoiced_this_month[0], datas, totals, \
               product_name, product_count, team_name, team_count, month, sale