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

import os
from flask import Flask, Blueprint
from .config import SEARCH_API_ENDPOINT_ENABLED


template_folder = os.getenv('BSK_API_TMPLTDIR', False)
if template_folder:
    app = Flask(__name__, template_folder = template_folder)
else:
    app = Flask(__name__)

app.config.from_object('api.config')

# Add in blueprints
from .resolver import resolver

blueprints = [resolver]

if SEARCH_API_ENDPOINT_ENABLED:
    from .search.server import searcher
    blueprints.append(searcher)

for blueprint in blueprints:
    app.register_blueprint(blueprint)

# make sure routes from api.server are included!

import api.server

