#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json
import random
import string

random.seed(47)

MIN_LEN, MAX_LEN = (1, 20)
MIN_NUM, MAX_NUM = (1, 100)

ALLOWED_CHARS = {
  'letters': string.ascii_letters,
  'lowercase': string.ascii_lowercase,
  'uppercase': string.ascii_uppercase,
  'digits': string.digits,
}

DEFAULT_PARAMS = {
  'chars': 'letters',
  'num': f'{MIN_NUM}',
  'len': f'{MIN_LEN}'
}


def lambda_handler(event, context):
  params = event['queryStringParameters'] if event.get('queryStringParameters', {}) else {}
  params.update({k: v for k, v in DEFAULT_PARAMS.items() if k not in params})

  char_type = params['chars']
  allowed_chars = ALLOWED_CHARS[char_type]

  num = min(max(int(params['num']), MIN_NUM), MAX_NUM)
  length = min(max(int(params['len']), MIN_LEN), MAX_LEN)

  ret = [''.join(random.choices(allowed_chars, k=length)) for _ in range(num)]

  return {
    'statusCode': 200,
    'body': json.dumps(ret)
  }


if __name__ == '__main__':
  event = {
    "resource": "/random/strings",
    "path": "/random/strings",
    "httpMethod": "GET",
    "headers": None,
    "multiValueHeaders": None,
    "queryStringParameters": {
      "chars": "letters", # [letters, lowercase, uppercase, digits]
      "num": "3",
      "len": "10"
    },
    "multiValueQueryStringParameters": {
      "chars": [
        "letters"
      ],
      "num": [
        "3"
      ],
      "len": [
        "10"
      ]
    },
    "pathParameters": None,
    "stageVariables": None,
    "requestContext": {
      "resourceId": "cwnr1x",
      "resourcePath": "/random/strings",
      "httpMethod": "GET",
      "extendedRequestId": "cV_t5H1EoAMFVQg=",
      "requestTime": "29/Nov/2022:03:16:27 +0000",
      "path": "/random/strings",
      "accountId": "111122223333",
      "protocol": "HTTP/1.1",
      "stage": "test-invoke-stage",
      "domainPrefix": "testPrefix",
      "requestTimeEpoch": 1669691787960,
      "requestId": "67e474a5-289e-4719-9eb7-a2417e9f442a",
      "identity": {
        "cognitoIdentityPoolId": None,
        "cognitoIdentityId": None,
        "apiKey": "test-invoke-api-key",
        "principalOrgId": None,
        "cognitoAuthenticationType": None,
        "userArn": "arn:aws:iam::111122223333:user/example",
        "apiKeyId": "test-invoke-api-key-id",
        "userAgent": "aws-internal/3 aws-sdk-java/1.12.336 Linux/5.4.214-134.408.amzn2int.x86_64 OpenJDK_64-Bit_Server_VM/25.352-b09 java/1.8.0_352 vendor/Oracle_Corporation cfg/retry-mode/standard",
        "accountId": "111122223333",
        "caller": "AIDACKCEVSQ6C2EXAMPLE",
        "sourceIp": "test-invoke-source-ip",
        "accessKey": "AKIAIOSFODNN7EXAMPLE",
        "cognitoAuthenticationProvider": None,
        "user": "AIDACKCEVSQ6C2EXAMPLE"
      },
      "domainName": "testPrefix.testDomainName",
      "apiId": "is8hw85n7h"
    },
    "body": None,
    "isBase64Encoded": False
  }
  #print(json.dumps(event, indent=2))

  ret = lambda_handler(event, None)
  print(ret)

