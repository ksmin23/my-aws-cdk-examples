#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json
import os

MESSAGE = os.getenv('MESSAGE', 'hello')


def lambda_handler(event, context):

  headers = event.get("headers", {})
  if headers.get("user-agent", "") != "ELB-HealthChecker/2.0":
    print("Incoming Event:", json.dumps(event))
  else:
    print("ELB-HealthChcker Event:", json.dumps(event))

  # TODO implement
  return {
    'body': f"<h1>{MESSAGE} from Lambda!</h1>",
    'statusCode': 200,
    'statusDescription': "200 OK",
    'isBase64Encoded': False,
    'headers': {
      "Content-Type": "text/html",
    },
  }


if __name__ == '__main__':
  http_event = {
    "requestContext": {
      "elb": {
        "targetGroupArn": "arn:aws:elasticloadbalancing:region:123456789012:targetgroup/my-target-group/6d0ecf831eec9f09"
      }
    },
    "httpMethod": "GET",
    "path": "/srcA/",
    "queryStringParameters": {
      "key1": "val1",
      "key2": "val2"
    },
    "headers": {
      "accept": "*/*",
      "host": "AlbLa-ALBAE-1SIOFWNPY2RP0-276077945.us-east-1.elb.amazonaws.com",
      "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6)",
      "x-amzn-trace-id": "Root=1-637d99ca-0eb2bd9830093293455987e2",
      "x-forwarded-for": "72.21.198.66",
      "x-forwarded-port": "80",
      "x-forwarded-proto": "http"
    },
    "body": "request_body",
    "isBase64Encoded": False
  }

  health_check_event = {
    "requestContext": {
      "elb": {
        "targetGroupArn": "arn:aws:elasticloadbalancing:region:123456789012:targetgroup/my-target-group/6d0ecf831eec9f09"
      }
    },
    "httpMethod": "GET",
    "path": "/",
    "queryStringParameters": {},
    "headers": {
      "user-agent": "ELB-HealthChecker/2.0"
    },
    "body": "",
    "isBase64Encoded": False
  }

  for event in [http_event, health_check_event]:
    lambda_handler(event, None)
    print()

