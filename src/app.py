from random import randint
from flask import Flask, jsonify
import boto3
from ssm_parameter_store import SSMParameterStore

import os
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path="{}/.env".format(current_dir))

app = Flask(__name__)

app.config.update(
    STORE=SSMParameterStore(
        prefix="{}/{}".format(os.environ.get('ssm_prefix'), os.environ.get('stage')),
        ssm_client=boto3.client('ssm', region_name=os.environ.get('region')),
        ttl=int(os.environ.get('ssm_ttl'))
    )
)


@app.route("/", methods=["GET"])
def hello():
    return "Hello from lambda"


@app.route("/random/<int:to_int>", methods=["GET"])
def get_random_quote(to_int):
    from_int = app.config['STORE']['from_int']
    return jsonify(randint(from_int, to_int))


if __name__ == '__main__':
    app.run()
