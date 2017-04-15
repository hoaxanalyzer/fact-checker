from __future__ import unicode_literals

import os
import sys
import logging
import json
import re
import itertools
import time

from flask import Flask, Response
from flask import request, abort
from flask_cors import CORS, cross_origin

import factcheck

application = Flask(__name__)
CORS(application)

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

@application.route("/")
def index():
	return "Hoax Analyzer - Query FactChecker API"

@application.route("/check", methods=['POST'])
def check():
	text = request.json['text']
	wc = factcheck.WikipediaCheck(text)
	result = {}
	result["code"], result["details"], result["is_negate"] = wc.check()
	logging.info("Finish wiki.check")
	result = json.dumps(result)
	return result

@application.after_request
def after_request(response):
	response.headers.add('Access-Control-Allow-Origin', '*')
	response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
	response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
	return response

if __name__ == "__main__":
	application.run(host="0.0.0.0", port=8095)