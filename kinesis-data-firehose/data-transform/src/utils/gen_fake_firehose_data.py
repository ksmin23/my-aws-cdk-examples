#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

from faker.providers import BaseProvider

class EventProvider(BaseProvider):
  all_event_types = [None, 'visit', 'view', 'cart', 'list', 'like', 'purchase', 'refund']

  def event_type(self):
    return self.random_element(self.all_event_types)

class AWSRegionProvider(BaseProvider):
  aws_regions = [
    None,
    'us-east-2',
    'us-east-1',
    'us-west-1',
    'us-west-2',
    'af-south-1',
    'ap-east-1',
    'ap-south-1',
    'ap-northeast-3',
    'ap-northeast-2',
    'ap-southeast-1',
    'ap-southeast-2',
    'ap-northeast-1',
    'ca-central-1',
    'eu-central-1',
    'eu-west-1',
    'eu-west-2',
    'eu-south-1',
    'eu-west-3',
    'eu-north-1',
    'me-south-1',
    'sa-east-1',
    'us-gov-east-1',
    'us-gov-west-1'
  ]

  def aws_region(self):
    return self.random_element(self.aws_regions)


if __name__ == '__main__':
  import argparse
  import datetime
  import itertools
  import random
  import sys
  import time

  import boto3
  from faker import Faker

  parser = argparse.ArgumentParser()

  parser.add_argument('--region-name', action='store', default='us-east-1',
    help='aws region name (default: us-east-1)')
  parser.add_argument('--stream-name', help='The name of the stream to put the data record into.')
  parser.add_argument('--max-count', default=10, type=int, help='The max number of records to put.')
  parser.add_argument('--dry-run', action='store_true')

  options = parser.parse_args()

  fake = Faker()

  fake.add_provider(EventProvider)
  fake.add_provider(AWSRegionProvider)
  fake.set_arguments('customer_id_format', {'string_format': '%###########'})
  fake.set_arguments('devices', {'elements': ['pc', 'mobile', 'tablet', None]})
  fake.set_arguments('event_start_datetime',
    {'start_datetime': datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)})

  DATA_COLUMNS = {
    'type': {
      'device': 'random_element:devices',
      'event': 'event_type'
    },
    'customer_id': 'pystr_format:customer_id_format',
    'event_timestamp': 'unix_time:event_start_datetime',
    'region': 'aws_region'
  }

  if not options.dry_run:
    firehose_client = boto3.client('firehose', region_name=options.region_name)

  predicate = (lambda x: x < options.max_count) if options.max_count >= 0 else (lambda x: x > options.max_count)
  for cnt in itertools.takewhile(predicate, itertools.count()):
    record = fake.json(data_columns=DATA_COLUMNS, num_rows=1)

    if options.dry_run:
      print(record, file=sys.stderr)
    else:
      res = firehose_client.put_record(
        DeliveryStreamName=options.stream_name,
        Record={
          'Data': record
        }
      )

      if (cnt + 1) % 100 == 0:
        print('[INFO] {} records are processed'.format(cnt+1), file=sys.stderr)

      if res['ResponseMetadata']['HTTPStatusCode'] != 200:
        print(res, file=sys.stderr)
    time.sleep(random.choices([0.01, 0.03, 0.05, 0.07, 0.1])[-1])
