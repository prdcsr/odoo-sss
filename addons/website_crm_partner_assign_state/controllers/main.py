import werkzeug
from odoo import http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.website_crm_partner_assign.controllers.main import WebsiteCrmPartnerAssign

from odoo.tools.translate import _


class WebsiteCrmPartnerAssignExtended(WebsiteCrmPartnerAssign):

    def sitemap_partners(env, rule, qs):
        if not qs or qs.lower() in '/partners':
            yield {'loc': '/partners'}

        Grade = env['res.partner.grade']
        dom = [('website_published', '=', True)]
        dom += sitemap_qs2dom(qs=qs, route='/partners/grade/', field=Grade._rec_name)
        for grade in env['res.partner.grade'].search(dom):
            loc = '/partners/grade/%s' % slug(grade)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

        partners_dom = [('is_company', '=', True), ('grade_id', '!=', False), ('website_published', '=', True),
                        ('grade_id.website_published', '=', True), ('country_id', '!=', False)]
        dom += sitemap_qs2dom(qs=qs, route='/partners/country/')
        countries = env['res.partner'].sudo().read_group(partners_dom, fields=['id', 'country_id'], groupby='country_id')
        for country in countries:
            loc = '/partners/country/%s' % slug(country['country_id'])
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    @http.route([
        '/partners',
        '/partners/page/<int:page>',

        '/partners/grade/<model("res.partner.grade"):grade>',
        '/partners/grade/<model("res.partner.grade"):grade>/page/<int:page>',

        '/partners/country/<model("res.country"):country>',
        '/partners/country/<model("res.country"):country>/page/<int:page>',

        '/partners/grade/<model("res.partner.grade"):grade>/country/<model("res.country"):country>',
        '/partners/grade/<model("res.partner.grade"):grade>/country/<model("res.country"):country>/page/<int:page>',

        '/partners/state/<model("res.country.state"):state>',
        '/partners/state/<model("res.country.state"):state>/page/<int:page>',

        '/partners/country/<model("res.country"):country>/state/<model("res.country.state"):state>',
        '/partners/country/<model("res.country"):country>/state/<model("res.country.state"):state>/page/<int:page>',

        '/partners/grade/<model("res.partner.grade"):grade>/state/<model("res.country.state"):state>',
        '/partners/grade/<model("res.partner.grade"):grade>/state/<model("res.country.state"):state>/page/<int:page>',

        '/partners/grade/<model("res.partner.grade"):grade>/country/<model("res.country"):country>/state/<model('
        '"res.country.state"):state>',
        '/partners/grade/<model("res.partner.grade"):grade>/country/<model("res.country"):country>/state/<model('
        '"res.country.state"):state>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=sitemap_partners)
    def partners(self, country=None, grade=None, state=None, page=0, **post):
        """
        Partially reused code from the controller of website_crm_partner_assign.
        Override the original method and add logic for state.
        """
        country_all = post.pop('country_all', False)
        partner_obj = request.env['res.partner']
        country_obj = request.env['res.country']
        search = post.get('search', '')

        base_partner_domain = [('is_company', '=', True), ('grade_id', '!=', False), ('website_published', '=', True)]
        if not request.env['res.users'].has_group('website.group_website_publisher'):
            base_partner_domain += [('grade_id.website_published', '=', True)]
        if search:
            base_partner_domain += ['|', ('name', 'ilike', search), ('website_description', 'ilike', search)]

        # group by grade
        grade_domain = list(base_partner_domain)
        if not country and not country_all:
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                country = country_obj.search([('code', '=', country_code)], limit=1)
        if country:
            grade_domain += [('country_id', '=', country.id)]
        if state:
            grade_domain += [('state_id', '=', state.id)]
        grades = partner_obj.sudo().read_group(
            grade_domain, ["id", "grade_id"],
            groupby="grade_id")
        grades_partners = partner_obj.sudo().search_count(grade_domain)
        # flag active grade
        for grade_dict in grades:
            grade_dict['active'] = grade and grade_dict['grade_id'][0] == grade.id
        grades.insert(0, {
            'grade_id_count': grades_partners,
            'grade_id': (0, _("All Categories")),
            'active': bool(grade is None),
        })

        # group by country
        country_domain = list(base_partner_domain)
        if grade:
            country_domain += [('grade_id', '=', grade.id)]
        if state:
            country_domain += [('state_id', '=', state.id)]
        countries = partner_obj.sudo().read_group(
            country_domain, ["id", "country_id"],
            groupby="country_id", orderby="country_id")
        countries_partners = partner_obj.sudo().search_count(country_domain)
        # flag active country
        for country_dict in countries:
            country_dict['active'] = country and country_dict['country_id'] and country_dict['country_id'][0] == country.id
        countries.insert(0, {
            'country_id_count': countries_partners,
            'country_id': (0, _("All Countries")),
            'active': bool(country is None),
        })

        states_domain = list(base_partner_domain)

        # current search
        if grade:
            base_partner_domain += [('grade_id', '=', grade.id)]
        if country:
            base_partner_domain += [('country_id', '=', country.id)]
        if state:
            base_partner_domain += [('state_id', '=', state.id)]

        # format pager
        if grade and not country and not state:
            url = '/partners/grade/' + slug(grade)
        elif country and not grade and not state:
            url = '/partners/country/' + slug(country)
        elif country and grade and not state:
            url = '/partners/grade/' + slug(grade) + '/country/' + slug(country)
        elif state and not grade and not country:
            url = '/partners/state/' + slug(state)
        elif state and grade and not country:
            url = '/partners/grade/' + slug(grade) + '/state/' + slug(state)
        elif state and grade and country:
            url = '/partners/grade/' + slug(grade) + '/country/' + slug(country) + '/state/' + slug(state)
        else:
            url = '/partners'
        url_args = {}
        if search:
            url_args['search'] = search
        if country_all:
            url_args['country_all'] = True

        if grade:
            states_domain += [('grade_id', '=', grade.id)]
        if country:
            states_domain += [('country_id', '=', country.id)]
        states = partner_obj.sudo().read_group(
            states_domain, ["id", "state_id"],
            groupby="state_id", orderby="state_id")
        states_partners = partner_obj.sudo().search_count(states_domain)
        for state_dict in states:
            state_dict['active'] = state and state_dict['state_id'] and state_dict['state_id'][0] == state.id
        states.insert(0, {
            'state_id_count': states_partners,
            'state_id': (0, _("Semua Provinsi")),
            'active': bool(state is None),
        })

        partner_count = partner_obj.sudo().search_count(base_partner_domain)
        pager = request.website.pager(
            url=url, total=partner_count, page=page, step=self._references_per_page, scope=7,
            url_args=url_args)

        # search partners matching current search parameters
        partner_ids = partner_obj.sudo().search(
            base_partner_domain, order="grade_sequence DESC, implemented_count DESC, display_name ASC, id ASC",
            offset=pager['offset'], limit=self._references_per_page)
        partners = partner_ids.sudo()

        google_map_partner_ids = ','.join(str(p.id) for p in partners)
        google_maps_api_key = request.website.google_maps_api_key

        values = {
            'countries': countries,
            'country_all': country_all,
            'current_country': country,
            'grades': grades,
            'current_grade': grade,
            'current_state': state,
            'states': states,
            'partners': partners,
            'google_map_partner_ids': google_map_partner_ids,
            'pager': pager,
            'searches': post,
            'search_path': "%s" % werkzeug.url_encode(post),
            'google_maps_api_key': google_maps_api_key,
        }
        return request.render("website_crm_partner_assign.index", values, status=partners and 200 or 404)