#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import argparse
import pprint
import random
import time

import boto3

random.seed(47)

SHARD_ITER_TYPE = ('TRIM_HORIZON', 'LATEST')

def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--stream-name', action="store", help='kinesis stream name')
  parser.add_argument('--shard-id', action="store", help='kinesis stream shard-id')
  parser.add_argument('--iter-type', choices=SHARD_ITER_TYPE, default='LATEST',
    help='kinesis stream shard iterator type: [{}]'.format(', '.join(SHARD_ITER_TYPE)))
  parser.add_argument('--region-name', action='store', default='us-east-1',
    help='aws region name (default: us-east-1)')

  options = parser.parse_args()

  stream_name, shard_iter_type = options.stream_name, options.iter_type

  kinesis_client = boto3.client('kinesis', region_name=options.region_name)
  response = kinesis_client.describe_stream(StreamName=stream_name)
  if options.shard_id:
    shard_id = options.shard_id
  else:
    shard_id_list = [e['ShardId'] for e in response['StreamDescription']['Shards']]
    shard_id = random.choice(shard_id_list)

  shard_iterator = kinesis_client.get_shard_iterator(StreamName=stream_name,
                                                     ShardId=shard_id,
                                                     ShardIteratorType=shard_iter_type)

  shard_iter = shard_iterator['ShardIterator']
  record_response = kinesis_client.get_records(ShardIterator=shard_iter, Limit=123)
  pprint.pprint(record_response.get('Records', []), indent=2)

  while 'NextShardIterator' in record_response:
    record_response = kinesis_client.get_records(ShardIterator=record_response['NextShardIterator'], Limit=123)
    pprint.pprint(record_response.get('Records', []), indent=2)

    # wait for a few seconds
    time.sleep(5)

if __name__ == '__main__':
  main()

