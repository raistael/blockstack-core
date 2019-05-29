#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
    Blockstack Core
    ~~~~~

    copyright: (c) 2014-2017 by Blockstack Inc.
    copyright: (c) 2017 by Blockstack.org

This file is part of Blockstack Core.

    Blockstack Core is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Blockstack Core is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Blockstack Core. If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import re
import os
import requests
import json
from collections import OrderedDict

from flask import Flask, jsonify, request, make_response
from flask import render_template, send_from_directory

from flask_crossdomain import crossdomain

from .parameters import parameters_required
from .utils import get_api_calls, cache_control
from .config import PUBLIC_NODE, PUBLIC_NODE_URL, BASE_API_URL, BASE_INDEXER_API_URL, DEFAULT_CACHE_TIMEOUT
from .config import SEARCH_NODE_URL, SEARCH_API_ENDPOINT_ENABLED, API_BLOCKCHAIN_URL, API_PROFILE_URL
from .config import PROXY_TIMEOUT

# hack around absolute paths
current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(current_dir + "/../")

sys.path.insert(0, parent_dir)

import blockstack
import virtualchain

blockstack_indexer_url = BASE_INDEXER_API_URL

if blockstack_indexer_url is None:
    blockstack_working_dir = blockstack.lib.config.default_working_dir()
    blockstack_config = blockstack.lib.load_configuration(blockstack_working_dir)
    blockstack_indexer_url = blockstack_config['blockstack-api']['indexer_url']

log = virtualchain.get_logger()

# Import app
from . import app

@app.after_request
def default_cache_off(response):
    """ By default turn front-end caching (i.e., nginx cache) off """
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-cache'
    return response

def forwarded_get(url, params = None):
    try:
        if params:
            resp = requests.get(url, params = params, allow_redirects=False, timeout=PROXY_TIMEOUT)
        else:
            resp = requests.get(url, allow_redirects=False, timeout=PROXY_TIMEOUT)
    except Exception as e:
        log.error("Exception proxying request to blockstack core: {}".format(e))
        return jsonify({'error': 'Server error processing request'}), 400

    try:
        log.debug("{} => {}".format(resp.url, resp.status_code))

        if resp.headers['content-type'] and 'application/json' in resp.headers['content-type']:
            respData = jsonify(resp.json())
        else:
            respData = resp.text

        if resp.status_code == 301:
            return respData, resp.status_code, resp.headers['Location']
        else:
            return respData, resp.status_code
    except Exception as e:
        log.error("Bad response from API URL: {} \n {}".format(resp.url, resp.text))
        return jsonify({'error': 'Not found'}), resp.status_code

@app.route('/v1/search', methods=['GET'])
@parameters_required(parameters=['query'])
@crossdomain(origin='*')
def search_people():
    query = request.values['query']

    if SEARCH_API_ENDPOINT_ENABLED:
        client = app.test_client()
        return client.get('/search?query={}'.format(query),
                          headers=list(request.headers))

    search_url = SEARCH_NODE_URL + '/search'

    try:
        resp = requests.get(url=search_url, params={'query': query}, timeout=PROXY_TIMEOUT)
    except (RequestsConnectionError, RequestsTimeout) as e:
        raise InternalProcessingError()

    data = resp.json()
    if not ('results' in data and isinstance(data['results'], list)):
        data = {'results': []}

    return jsonify(data), 200

@app.route('/v1/index_files/blockchain', methods=['GET'])
@cache_control(10*60)
@crossdomain(origin='*')
def fetch_index_blockchain_files():
    if API_BLOCKCHAIN_URL and API_PROFILE_URL:
        response = make_response((jsonify({ 'blockchainData': API_BLOCKCHAIN_URL }), 302))
        response.headers['Location'] = API_BLOCKCHAIN_URL
        return response
    else:
        err = { 'error': 'Index file serving not configured on this server.' }
        return jsonify(err), 404

@app.route('/v1/index_files/profiles', methods=['GET'])
@cache_control(10*60)
@crossdomain(origin='*')
def fetch_index_profile_files():
    if API_BLOCKCHAIN_URL and API_PROFILE_URL:
        response = make_response((jsonify({ 'profileData': API_PROFILE_URL }), 302))
        response.headers['Location'] = API_PROFILE_URL
        return response
    else:
        err = { 'error': 'Index file serving not configured on this server.' }
        return jsonify(err), 404

CACHE_SPECIFIC = [ re.compile(regex) for regex in
                   [r'^/v1/node/ping/?$',
                    r'^/v1/accounts/[\w\.]+/history/?$',
                    r'^/v1/blockchains/bitcoin/consensus/?$',
                    r'^/v1/names/[\w\.]+/?$'] ]

SPECIFIED = {
    0 : 'public, max-age=30',
    1 : 'public, max-age=60',
    2 : 'public, max-age=30',
    3 : 'public, max-age=300' }


@app.route('/<path:path>', methods=['GET'])
@crossdomain(origin='*')
def catch_all_get(path):
    API_URL = BASE_API_URL + '/' + path
    params = dict(request.args)

    log.debug('Begin ' + path)
    inner_resp = forwarded_get(API_URL, params = params)
    resp = make_response(inner_resp[:2])

    if len(inner_resp) > 2 and inner_resp[1] == 301:
        resp.headers['Location'] = inner_resp[2]

    for ix, matcher in enumerate(CACHE_SPECIFIC):
        if matcher.match('/' + path):
            if ix in SPECIFIED:
                resp.headers['Cache-Control'] = SPECIFIED[ix]
            return resp

    resp.headers['Cache-Control'] = 'public, max-age={:d}'.format(30*60)
    return resp

@app.route('/<path:path>', methods=['POST'])
def catch_all_post(path):

    if PUBLIC_NODE:
        return render_template('403.html'), 403

    API_URL = BASE_API_URL + '/' + path

    resp = requests.post(API_URL, data=requests.data, timeout=PROXY_TIMEOUT)

    return jsonify(resp.json()), 200

@app.route('/')
@cache_control(10*60)
def index():
    server_info = blockstack.lib.client.getinfo(hostport=blockstack_indexer_url)
    return render_template('index.html',
                           server_info=server_info,
                           server_url=PUBLIC_NODE_URL)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico')


"""
@app.errorhandler(500)
def internal_error(error):
    return make_response(jsonify({'error': error.description}), 500)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)
"""
