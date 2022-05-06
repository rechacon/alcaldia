import asyncio
from datetime import datetime
from odoo import models, fields, api, _
from bs4 import BeautifulSoup
from pytz import timezone
import requests
from requests.adapters import HTTPAdapter


from logging import getLogger

_logger = getLogger(__name__)


class ResCurrencyExchangeRate(models.Model):
    _name = "res.currency.exchange.rate"
    _description = "Exchange Rate"

    name = fields.Many2one('res.currency', string='Money')
    server = fields.Selection([('bcv', 'Banco Central de Venezuela')])
    currency_ids = fields.Many2many('res.currency.rate',
                                    compute='_compute_res_currency',
                                    string='Rate')

    async def sunacrip_async(self):
        """Get the dollar rate from sunacrip"""
        headers = {'Content-type': 'application/json'}
        data = '{"coins":["%s"], "fiats":["USD"]}' % (self.name.name)

        session = requests.session()
        session.keep_alive = False
        session.mount('http://petroapp-price.petro.gob.ve/price/', HTTPAdapter(max_retries=5))
        session.mount('https://petroapp-price.petro.gob.ve/price/', HTTPAdapter(max_retries=5))

        response = session.post('https://petroapp-price.petro.gob.ve/price/',
                                headers=headers, data=data, verify=False)

        check = response.json()

        if check['status'] == 200 and check['success']:
            check = float(check['data']['' + self.name.name + '']['USD'])
            return check
        return False

    def sunacrip(self):
        """Get the dollar rate from sunacrip"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.sunacrip_async())

    def central_bank(self):
        """Get the dollar rate from bcv"""
        url = "http://www.bcv.org.ve/"
        content = requests.get(url)

        status_code = content.status_code
        if status_code == 200:
            html = BeautifulSoup(content.text, "html.parser")
            # Euro
            euro = html.find('div', {'id': 'euro'})
            euro = str(euro.find('strong')).split()
            euro = str.replace(euro[1], '.', '')
            euro = float(str.replace(euro, ',', '.'))
            # Dolar
            dolar = html.find('div', {'id': 'dolar'})
            dolar = str(dolar.find('strong')).split()
            dolar = str.replace(dolar[1], '.', '')
            dolar = float(str.replace(dolar, ',', '.'))

            if self.name.name == 'USD':
                return dolar
            if self.name.name == 'EUR':
                return euro
            return False
        return False

    def dtoday(self):
        """Get the dollar rate from dollar today"""
        url = "https://s3.amazonaws.com/dolartoday/data.json"
        response = requests.get(url)
        status_code = response.status_code

        if status_code == 200:
            response = response.json()
            usd = float(response['USD']['transferencia'])
            eur = float(response['EUR']['transferencia'])

            if self.name.name == 'USD':
                return usd
            if self.name.name == 'EUR':
                return eur
            return False
        return False

    def set_rate(self):
        """Set exchange rate"""
        if self.server == 'bcv':
            currency = self.central_bank()
        elif self.server == 'dolar_today':
            currency = self.dtoday()
        elif self.server == 'sunacrip':
            currency = self.sunacrip()
        rate = self.env['res.currency.rate'].search([('name', '=', datetime.now()),
                                                     ('currency_id', '=', self.name.id)])
        _logger.info(f'\n\n Rate: %s {currency} \n\n')
        if len(rate) == 0:
            self.env['res.currency.rate'].create({
                'currency_id': self.name.id,
                'name': datetime.now(),
                'sell_rate': round(currency, 2),
                'inverse_company_rate': round(currency, 2),
                'rate': 1 / round(currency, 2)
            })
        elif len(rate) == 1:
            if rate.name.strftime('%Y-%m-%d') == datetime.now().strftime('%Y-%m-%d'):
                rate.write({
                    'sell_rate': round(currency, 2),
                    'inverse_company_rate': round(currency, 2),
                    'rate': 1 / round(currency, 2)
                })
            else:
                self.env['res.currency.rate'].create({
                    'currency_id': self.name.id,
                    'name': datetime.now(),
                    'sell_rate': round(currency, 2),
                    'inverse_company_rate': round(currency, 2),
                    'rate': 1 / round(currency, 2)
                })

    @api.model
    def _cron_update_product(self):
        exchange = self.env['res.currency.exchange.rate'].search([])
        for rec in exchange:
            rec.set_rate()

    @api.model
    def _compute_res_currency(self):
        for rec in self:
            rate = self.env['res.currency.rate'].search([
                ('currency_id', '=', rec.name.id), ])
            rec.currency_ids = rate


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    sell_rate = fields.Float(string='Exchange rate', digits=(12, 4))
    currency_id = fields.Many2one(readonly=False)

    @api.constrains("sell_rate")
    def set_sell_rate(self):
        """Set the sale rate"""
        self.rate = 1 / self.sell_rate

    def get_systray_dict(self, date):
        tz_name = "America/Caracas"
        today_utc = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        context_today = today_utc.astimezone(timezone(tz_name))
        date = context_today.strftime("%Y-%m-%d")
        rate = self.env['res.currency.rate'].search([
            ('currency_id', '=', 2),
            ('name', '=', date)], limit=1).sorted(lambda x: x.name)
        if rate:
            exchange_rate = 1 / rate.rate
            return {'date': _('Date : ') + rate.name.strftime("%d/%m/%Y"), 'rate': "Bs/USD: " + str("{:,.2f}".format(exchange_rate))}
        return {'date': _('No currency rate for ') + context_today.strftime("%d/%m/%Y"), 'rate': 'N/R'}
