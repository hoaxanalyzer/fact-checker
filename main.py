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

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

@application.route("/")
def index():
	return "Hoax Analyzer - Query FactChecker API"

@application.route("/check", methods=['POST'])
def extract_text():
	try:
		text = request.json['text']
		wc = factcheck.WikipediaCheck(text)
		result = {}
		result["code"], result["details"], result["is_negate"] = wc.check()
		result = json.dumps(result)
	except Exception as e:
		result = json.dumps({"status": "Failed", "message": "Incorrect parameters", "details": str(e)})
	return result

@application.after_request
def after_request(response):
	response.headers.add('Access-Control-Allow-Origin', '*')
	response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
	response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
	return response

if __name__ == "__main__":
	application.run(host="0.0.0.0", port=8095)