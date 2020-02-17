import logging
import math
import os
import sys
import time

import click
import requests

from prometheus_client import start_http_server, Gauge
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class RulesExporter():
    '''
    The RulesExporter collect metrics and alerts to create a prometheus metric page.

    Args:
        url_inventory (str): unity inventory url 
        token (str): bear token to authentificate in the inventory api
        port (int): listen port of http server
        log (str): log level (debug, info, error)
        inventory_api_batch_size (int): size of batch in paginated api call
        env (str): envrinoment
    '''
    __slots__ = [
        'url_inventory',
        'url_promehteus',
        'token',
        'env',
        'log',
        'port',
        'inventory_api_batch_size',
        'gauge'
    ]

    def __init__(self, url_inventory, url_promehteus, token, env, port=8000, log_level='info', inventory_api_batch_size=500):
        self._init_logging(log_level=log_level)
        self.log.info('Initialisation of the rules exporter')
        if not url_inventory:
            self.log.critical(f'Inventory url not found')
            sys.exit(128)

        if not url_promehteus:
            self.log.critical('Prometheus url not found')
            sys.exit(128)

        if not token:
            self.log.critical(f'Parameters token not found')
            sys.exit(128)

        if not env:
            self.log.critical(f'Parameters env not found')
            sys.exit(128)

        self.inventory_api_batch_size = inventory_api_batch_size
        self.url_inventory = url_inventory
        self.url_promehteus = url_promehteus

        if env == "test":
            self.env = "int"
        else:
            self.env = env

        self.token = token
        self.port = int(port)
        self.gauge = Gauge(
            'CLOUD_ALERTS',
            'List of rules',
            ['env', 'alertname', 'service', 'type', 'alertstate'],
        )

    def start_http_server(self):
        ''' 
        Start the http server to publish prometheus metric page on the root.
        '''
        self.log.info(f'Starting the web server on port {self.port}')
        start_http_server(self.port)
        while True:
            self._process_request()
            time.sleep(60)

    def _init_logging(self, log_level='info'):
        '''
        Initialize the logging service.

        Args:
            log_level (str): log level (debug, info, error)
        '''
        level = self._get_log_level(log_level)
        logging.basicConfig(
            format='%(asctime)s-%(levelname)s: %(message)s',
            level=level)
        self.log = logging.getLogger()
        self.log.debug(f'Log level to debug')

    def _get_log_level(self, log_level):
        '''
        Get the log level in string and return the log level enum value.

        Args:
            log_level (str): log level (debug, info, error)

        Return:
            int: log level

        '''
        level = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'error': logging.ERROR
        }
        return level.get(log_level, logging.INFO)

    def _process_request(self):
        '''
        Get all data and generate the metrics page.
        '''
        self.log.info(f'Get rules on {self.url_inventory}')
        rules = self._get_rules()
        alerts = self._get_alertes_triggered()
        self._generate_metric(self._filter_rules(rules), alerts)

    def _filter_rules(self, rules):
        '''
        Get list of of rules and return rule filter by labels (type=cloud_health && service).

        Args:
            rules (list): List of rules form the inventory api

        Return:
            list: List of rules filtered
        '''
        return [
            rule
            for rule in rules
            if rule['labels'].get('type') == 'cloud_health' and 'service' in rule['labels']
        ]

    def _get_rules(self):
        '''
        Get rules on the inventory api.

        Return:
            list: List of rules form the inventory api
        '''
        alerts = self._get_request_paginated(
            self.url_inventory+'/api/inventory/alert-rules')
        return alerts

    def _get_alertes_triggered(self):
        '''
        Get alerts firing on the promtheus api.

        Return:
            list: List of all alerts form prometheus
        '''
        payload = {
            'dedup': 'true',
            'query':  'ALERTS{alertstate="firing"}'
        }

        response = self._get_request(
            self.url_promehteus + '/api/v1/query', payload)

        return response['data']['result']

    def _get_request_paginated(self, url):
        '''
        Make GET request with pagination.

        Args:
            url (str): full api url to reach

        Return:
            list: all items contacted in one list
        '''
        page = 1
        result = []

        while True:
            self.log.debug(f'Get page {page} by batch of {url}')
            payload = {
                'pageSize': self.inventory_api_batch_size,
                'page': page,
                'env': self.env
            }

            data = self._get_request(url, payload)
            result.extend(data['items'])
            if page >= math.ceil(data['total']/self.inventory_api_batch_size):
                break
            page += 1
        return result

    def _get_request(self, url, payload):
        '''
        Make a GET request to an api with a payload.

        Args:
            url (str): api url to reach
            payload (dict): payload to add in the request

        Return:
            dict: Json of the result
        '''
        session = requests.Session()

        header = {'Authorization': f'Bearer {self.token}'}

        retries = Retry(total=100, backoff_factor=5,
                        status_forcelist=[502, 503, 504])

        session.mount('https://', HTTPAdapter(max_retries=retries))

        response = session.get(url=url,
                               headers=header, params=payload)

        if response.status_code == 401:
            self.log.error(
                f'Authentification failed with token on {url}.')
            exit(1)

        response.raise_for_status()

        data = response.json()
        return data

    def _generate_metric(self, rules, alerts):
        ''' 
        Generate prometheus metrics collections with the rules and the alerts.

        Args:
            rules (list): list of all rules
            alerts (list): list of all alerts
        '''
        self.gauge._metrics.clear()
        for rule in rules:
            for env in rule['env']:
                if env == "int":
                    env = "test"
                state = 'up'
                alerts_count = 0
                for alert in list(alerts):
                    if rule['id'] == alert['metric']['ruleId']:
                        state = 'firing'
                        alerts_count += 1
                        alerts.remove(alert)
                self.gauge.labels(env, rule['alert'], rule['labels'].get('service'),
                                  rule['labels'].get('type'), state).set(alerts_count)


@click.command()
@click.option('--url-inventory', '-u', required=True, help='Base url to reach the inventory. env var INVENTORY_URL', envvar='INVENTORY_URL')
@click.option('--url-promehteus', '-m', required=True, help='Base url to reach the the prometheus. env var PROMETHEUS_URL', envvar='PROMETHEUS_URL')
@click.option('--token', '-t', required=True, help='Bear token to get authentificate to the inventory. env var INVENTORY_TOKEN', envvar='INVENTORY_TOKEN')
@click.option('--env', '-e', required=True, help='Environment for rules. env var INVENTORY_ENV', envvar='INVENTORY_ENV')
@click.option('--listen-port', '-p', default=8000, help='Port where the prometheus page will be publish (default=8000) or env var EXPORTER_PORT', envvar='EXPORTER_PORT')
@click.option('--log-level', '-l', default='info', help='Log level can be: debug, info, error (default=info) or env var LOG_LEVEL', envvar='LOG_LEVEL')
def rules_exporter(url_inventory, url_promehteus, env, token, listen_port, log_level):
    exporter = RulesExporter(url_inventory, url_promehteus, token, env,
                             port=listen_port, log_level=log_level)
    exporter.start_http_server()


if __name__ == '__main__':
    rules_exporter()
