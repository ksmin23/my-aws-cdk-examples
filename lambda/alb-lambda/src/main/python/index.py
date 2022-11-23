#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json


def lambda_handler(event, context):
  print("Incoming Event:", json.dumps(event))

  # TODO implement
  return {
    'body': "<h1>Hello from Lambda!</h1>",
    'statusCode': 200,
    'statusDescription': "200 OK",
    'isBase64Encoded': False,
    'headers': {
      "Content-Type": "text/html",
    },
  }

