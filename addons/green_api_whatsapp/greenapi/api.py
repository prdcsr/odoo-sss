from odoo import _
from odoo.exceptions import Warning
import json
import requests


class GreenApi(object):
    def __init__(self, id_instance, api_token_instance, **kwargs):
        self.APIUrl = 'https://7103.api.greenapi.com/'
        self.id_instance = id_instance or ''
        self.api_token_instance = api_token_instance or ''

    def auth(self):
        # if not self.id_instance and not self.api_token_instance:
        #    raise UserError(_('Warning! Please add Key and Secret Whatsapp API on General Settings'))
        try:
            requests.get(self.APIUrl + 'waInstance' + self.id_instance + '/getStateInstance/' + self.api_token_instance,
                         headers={'Content-Type': 'application/json'})
        except requests.exceptions as err:
            raise Warning(_('Error! Could not connect to Whatsapp account. %s') % err)
        # except (requests.exceptions.HTTPError,
        #         requests.exceptions.RequestException,
        #         requests.exceptions.ConnectionError) as err:

    def get_instance_status(self):
        try:
            request_url = self.APIUrl + 'waInstance' + self.id_instance + "/getStateInstance/" + self.api_token_instance
            data_req = requests.get(
                request_url,
                headers={'Content-Type': 'application/json'})
            if data_req.status_code != 400:
                res = json.loads(data_req.text)
                return res or {}
            else:
                raise requests.exceptions.RequestException(json.dumps({
                    'message': data_req.text if isinstance(data_req.text, str) else json.dumps({
                        'message': data_req.text}),
                    'request_url': request_url
                }))
        except (requests.exceptions.HTTPError,
                requests.exceptions.RequestException,
                requests.exceptions.ConnectionError) as err:
            raise Warning(_('Error! Could not connect to Whatsapp account. %s') % err)

    def get_instance_setting(self):
        try:
            request_url = self.APIUrl + 'waInstance' + self.id_instance + "/getSettings/" + self.api_token_instance
            data_req = requests.get(
                request_url,
                headers={'Content-Type': 'application/json'})
            if data_req.status_code != 400:
                res = json.loads(data_req.text)
                return res or {}
            else:
                raise requests.exceptions.RequestException(json.dumps({
                    'message': data_req.text if isinstance(data_req.text, str) else json.dumps({
                        'message': data_req.text}),
                    'request_url': request_url
                }))
        except (requests.exceptions.HTTPError,
                requests.exceptions.RequestException,
                requests.exceptions.ConnectionError) as err:
            raise Warning(_('Error! Could not connect to Whatsapp account. %s') % err)

    def get_instance_qr_code(self):
        try:
            request_url = self.APIUrl + 'waInstance' + self.id_instance + "/qr/" + self.api_token_instance
            data_req = requests.get(
                request_url,
                headers={'Content-Type': 'application/json'})
            if data_req.status_code != 400:
                res = json.loads(data_req.text)
                return res or {}
            else:
                raise requests.exceptions.RequestException(json.dumps({
                    'message': data_req.text if isinstance(data_req.text, str) else json.dumps({
                        'message': data_req.text}),
                    'request_url': request_url
                }))
        except (requests.exceptions.HTTPError,
                requests.exceptions.RequestException,
                requests.exceptions.ConnectionError) as err:
            raise Warning(_('Error! Could not connect to Whatsapp account. %s') % err)

    def send_message_file(self, data, files):
        try:
            request_url = self.APIUrl + 'waInstance' + self.id_instance + "/sendFileByUpload/" + self.api_token_instance
            data_req = requests.post(
                request_url,
                files=files, data=data,
                headers={})
            if data_req.status_code != 400:
                res = json.loads(data_req.text)
                res['request_url'] = request_url
                return res or {}
            else:
                raise requests.exceptions.RequestException(json.dumps({
                    'message': data_req.text if isinstance(data_req.text, str) else json.dumps({
                        'message': data_req.text}),
                    'data': data,
                    'request_url': request_url
                }))
        except (requests.exceptions.HTTPError,
                requests.exceptions.RequestException,
                requests.exceptions.ConnectionError) as err:
            raise Warning(_('Error! Could not connect to Whatsapp account. %s') % err)

    def send_message_text(self, data):
        try:
            request_url = self.APIUrl + 'waInstance' + self.id_instance + "/sendMessage/" + self.api_token_instance
            data_req = requests.post(
                request_url,
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'})
            if data_req.status_code is not None and data_req.status_code != 400:
                res = json.loads(data_req.text)
                res['request_url'] = request_url
                return res or {}
            else:
                raise requests.exceptions.RequestException(json.dumps({
                    'message': data_req.text if isinstance(data_req.text, str) else json.dumps({
                        'message': data_req.text}),
                    'data': data,
                    'request_url': request_url
                }))

        except (requests.exceptions.HTTPError,
                requests.exceptions.RequestException,
                requests.exceptions.ConnectionError) as err:
            raise Warning(_('Error! Could not connect to Whatsapp account. %s') % err)

    def instance_logout(self):
        try:
            request_url = self.APIUrl + 'waInstance' + self.id_instance + "/logout/" + self.api_token_instance
            data_req = requests.get(
                self.APIUrl + 'waInstance' + self.id_instance + "/logout/" + self.api_token_instance,
                headers={'Content-Type': 'application/json'})
            if data_req.status_code != 400:
                res = json.loads(data_req.text)
                return res or {}
            else:
                raise requests.exceptions.RequestException(json.dumps({
                    'message': data_req.text if isinstance(data_req.text, str) else json.dumps({
                        'message': data_req.text}),
                    'request_url': request_url
                }))
        except (requests.exceptions.HTTPError,
                requests.exceptions.RequestException,
                requests.exceptions.ConnectionError) as err:
            raise Warning(_('Error! Could not connect to Whatsapp account. %s') % err)

    def get_count(self):
        data = {}
        url = self.APIUrl + 'count/' + self.id_instance + '/' + self.api_token_instance
        data_req = requests.get(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
        res = json.loads(data_req.text)
        # print ('===res===',res)
        return res.get('result') and res['result'] or {}

    def get_limit(self):
        data = {}
        url = self.APIUrl + 'limit/' + self.id_instance + '/' + self.api_token_instance
        data_req = requests.get(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
        res = json.loads(data_req.text)
        # print ('===res===',res)
        return res.get('result') and res['result'] or {}

    def get_request(self, method, data):
        url = self.APIUrl + 'get/' + self.id_instance + '/' + self.api_token_instance + '/' + method
        data_req = requests.get(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
        res = json.loads(data_req.text)
        return res.get('result') and res['result'] or {}

    def post_request(self, method, data):
        url = self.APIUrl + 'post/'
        data = json.loads(data)
        data['instance'] = self.id_instance
        data['key'] = self.api_token_instance
        data['method'] = method
        # get_version = request.env["ir.module.module"].sudo().search([('name','=','base')], limit=1)
        # data['get_version'] = get_version and get_version.latest_version
        data_s = {
            'params': data
        }
        response = requests.post(url, json=data_s, headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            message1 = json.loads(response.text)
            message = message1.get('result').get('message')
            chatID = message.get('id') and message.get('id').split('_')[1]
            return {'chatID': chatID, 'message': message}
        else:
            return {'message': {'sent': False, 'message': 'Error'}}

    def get_phone(self, method, phone):
        data = {}
        url = self.APIUrl + 'phone/' + self.id_instance + '/' + self.api_token_instance + '/' + method + '/' + phone
        data = requests.get(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
        res = json.loads(data.text)
        return res.get('result') and res['result'] or {}
