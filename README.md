## Playing with lambda, serverless and Python

Couple of weeks ago I attended to [serverless course](https://theserverlesscourse.com/). I've played with lambdas from time to time (basically when AWS forced me to use them) but without knowing exactly what I was doing. After this course I know how to work with the serverless framework and I understand better lambda world. Today I want to hack a little bit and create a simple Python service to obtain random numbers. Let's start

We don't need Flask to create lambdas but as I'm very comfortable with it so we'll use it here.
Basically I follow the steps that I've read [here](https://medium.com/@Twistacz/flask-serverless-api-in-aws-lambda-the-easy-way-a445a8805028)

```python
from flask import Flask

app = Flask(__name__)


@app.route("/", methods=["GET"])
def hello():
    return "Hello from lambda"


if __name__ == '__main__':
    app.run()
```

And serverless yaml to configure the service

```yaml
service: random

plugins:
  - serverless-wsgi
  - serverless-python-requirements
  - serverless-pseudo-parameters

custom:
  defaultRegion: eu-central-1
  defaultStage: dev
  wsgi:
    app: app.app
    packRequirements: false
  pythonRequirements:
    dockerizePip: non-linux

provider:
  name: aws
  runtime: python3.7
  region: ${opt:region, self:custom.defaultRegion}
  stage: ${opt:stage, self:custom.defaultStage}

functions:
  home:
    handler: wsgi_handler.handler
    events:
      - http: GET /
```

We're going to use serverless plugins. We need to install them:
```

npx serverless plugin install -n serverless-wsgi
npx serverless plugin install -n serverless-python-requirements
npx serverless plugin install -n serverless-pseudo-parameters
```

And that's all. Our "Hello world" lambda service with Python and Flask is up and running.
Now We're going to create a "more complex" service. We're going to return a random number with random.randint function. 
randint requires two parameters: start, end. We're going to pass the end parameter to our service. The start value will be parametrized. I'll parametrize it only because I want to play with AWS's Parameter Store ([SSM](https://medium.com/@nqbao/how-to-use-aws-ssm-parameter-store-easily-in-python-94fda04fea84)). It's just an excuse.

Let's start with the service:
```python
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
```

Now the serverless configuration. I can use only one function, handling all routes and letting Flask do the job.
```yaml
functions:
  app:
    handler: wsgi_handler.handler
    events:
      - http: ANY /
      - http: 'ANY {proxy+}'
```

But in this example I want to create two different functions. Only for fun (and to use different role statements and different logs in cloudwatch).

```yaml
service: random

plugins:
  - serverless-wsgi
  - serverless-python-requirements
  - serverless-pseudo-parameters
  - serverless-iam-roles-per-function

custom:
  defaultRegion: eu-central-1
  defaultStage: dev
  wsgi:
    app: app.app
    packRequirements: false
  pythonRequirements:
    dockerizePip: non-linux

provider:
  name: aws
  runtime: python3.7
  region: ${opt:region, self:custom.defaultRegion}
  stage: ${opt:stage, self:custom.defaultStage}
  memorySize: 128
  environment:
    region: ${self:provider.region}
    stage: ${self:provider.stage}

functions:
  app:
    handler: wsgi_handler.handler
    events:
      - http: ANY /
      - http: 'ANY {proxy+}'
    iamRoleStatements:
      - Effect: Allow
        Action: ssm:DescribeParameters
        Resource: arn:aws:ssm:${self:provider.region}:#{AWS::AccountId}:*
      - Effect: Allow
        Action: ssm:GetParameter
        Resource: arn:aws:ssm:${self:provider.region}:#{AWS::AccountId}:parameter/random/*
  home:
    handler: wsgi_handler.handler
    events:
      - http: GET /
```
 
And that's all. "npx serverless deploy" and my random generator is running.  




