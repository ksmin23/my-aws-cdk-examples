#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import argparse
import json

import boto3


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--region-name', action='store', default='us-east-1',
    help='aws region name (default: us-east-1)')
  parser.add_argument('--on-failure', action='store_true')

  options = parser.parse_args()

  cfn_client = boto3.client('cloudformation', region_name=options.region_name)
  res = cfn_client.describe_stacks(StackName='LambdaAsyncInvokeStack')['Stacks'][0]['Outputs']
  stack_outputs = {e['OutputKey']: e['OutputValue'] for e in res}

  sns_client = boto3.client('sns', region_name=options.region_name)
  sns_topic_arn = stack_outputs['SNSTopicArn']

  subject = 'On_Failure' if options.on_failure else 'On_Success'
  message = 'Hello SNS!'
  print(json.dumps({'Subject': subject, 'Message': message}, indent=2), '\n')

  res = sns_client.publish(TopicArn=sns_topic_arn,
    Subject=subject,
    Message=message)
  print(json.dumps(res, indent=2))


if __name__ == '__main__':
  main()

