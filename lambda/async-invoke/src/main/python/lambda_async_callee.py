#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json

def lambda_handler(event, context):
  print("[InvocationRecord]\n", json.dumps(event))

  # TODO implement
  return {
      'statusCode': 200,
      'body': json.dumps('Hello from Lambda!')
  }
