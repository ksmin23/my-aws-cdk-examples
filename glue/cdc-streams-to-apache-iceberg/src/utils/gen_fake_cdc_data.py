#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import argparse
import json
import random
import time
import typing
import datetime

import boto3
import diskcache
from mimesis.locales import Locale
from mimesis.schema import Field, Schema
from mimesis.providers.base import BaseProvider


class CustomDatetimeProvider(BaseProvider):
  class Meta:
    """Class for metadata."""
    name: typing.Final[str] = "custom_datetime"

  def __init__(self, seed=47) -> None:
    super().__init__(seed=seed)
    self.random = random.Random(seed)

  def formated_datetime(self, fmt='%Y-%m-%dT%H:%M:%SZ', lt_now=False) -> str:
    CURRENT_YEAR = datetime.datetime.now().year
    CURRENT_MONTH = datetime.datetime.now().month
    CURRENT_DAY = datetime.datetime.now().day
    CURRENT_HOUR = datetime.datetime.now().hour
    CURRENT_MINUTE = datetime.datetime.now().minute
    CURRENT_SECOND = datetime.datetime.now().second

    if lt_now:
      random_time = datetime.time(
        self.random.randint(0, CURRENT_HOUR),
        self.random.randint(0, max(0, CURRENT_MINUTE-1)),
        self.random.randint(0, max(0, CURRENT_SECOND-1)),
        self.random.randint(0, 999999)
      )
    else:
      random_time = datetime.time(
        CURRENT_HOUR,
        CURRENT_MINUTE,
        self.random.randint(CURRENT_SECOND, 59),
        self.random.randint(0, 999999)
      )

    datetime_obj = datetime.datetime.combine(
      date=datetime.date(CURRENT_YEAR, CURRENT_MONTH, CURRENT_DAY),
      time=random_time,
    )

    return datetime_obj.strftime(fmt)


def get_updated_or_deleted_record(record, cache, expire=3600):
  key_list = [k for k in cache.iterkeys()]
  if not key_list:
    return record

  k = random.choice(key_list)
  updated_or_deleted_record = json.loads(cache.get(k))
  operation = 'update' if random.randint(0, 1) % 2 else 'delete'
  if operation == 'delete':
     updated_or_deleted_record['metadata'] = record['metadata']
     updated_or_deleted_record['metadata']['operation'] = 'delete'
  else:
     updated_or_deleted_record['data']['amount'] = record['data']['amount']
     updated_or_deleted_record['data']['trans_datetime'] = record['data']['trans_datetime']
     updated_or_deleted_record['metadata'] = record['metadata']
     updated_or_deleted_record['metadata']['operation'] = 'update'

  cache.set(k, json.dumps(updated_or_deleted_record), expire)
  return updated_or_deleted_record


def main(options, trans_cache):
  _ = Field(locale=Locale.EN, providers=[CustomDatetimeProvider])

  _schema = Schema(schema=lambda: {
    "data": {
      "trans_id": _("integer_number", start=1, end=12345),
      "customer_id": str(_("integer_number", start=123456789012, end=999999999999)),
      "event": _("choice", items=['visit', 'view', 'list', 'like', 'cart', 'purchase']),
      "sku": _("pin", mask='@@####@@@@'),
      "amount":  _("integer_number", start=1, end=10),
      "device": _("choice", items=['pc', 'mobile', 'tablet']),
      "trans_datetime": _("custom_datetime.formated_datetime", lt_now=True),
    },
    "metadata": {
      "timestamp": _("custom_datetime.formated_datetime", fmt="%Y-%m-%dT%H:%M:%S.%fZ"),
      "record-type": "data",
      "operation": "insert",
      "partition-key-type": "primary-key",
      "schema-name": options.database,
      "table-name": options.table,
      "transaction-id": _("integer_number", start=123456789012, end=999999999999)
    }
  })

  if not options.dry_run:
    kinesis_streams_client = boto3.client('kinesis', region_name=options.region_name)

  cnt = 0
  for record in _schema.iterator(options.max_count):
    cnt += 1

    with diskcache.Cache(trans_cache.directory) as cache:
      if options.cdc_type == 'insert-only':
        if random.randint(0, 99) % 2 == 0:
          key = record['data']['trans_id']
          cache.set(key, f"{json.dumps(record)}", expire=options.ttl_sec)
      elif random.randint(0, 99) % 2 == 0:
        record = get_updated_or_deleted_record(record, cache, expire=options.ttl_sec)

    partition_key = str(record['data']['trans_id'])
    record = json.dumps(record)
    if options.dry_run:
      print(record)
    else:
      res = kinesis_streams_client.put_record(
        StreamName=options.stream_name,
        Data=f"{record}\n", # convert JSON to JSON Line
        PartitionKey=partition_key
      )

      if options.console:
        print(record)

      if cnt % 100 == 0:
        print(f'[INFO] {cnt} records are processed', file=sys.stderr)

      if res['ResponseMetadata']['HTTPStatusCode'] != 200:
        print(res, file=sys.stderr)
    time.sleep(random.choices([0.01, 0.03, 0.05, 0.07, 0.1])[-1])
  print(f'[INFO] Total {cnt} records are processed', file=sys.stderr)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()

  parser.add_argument('--region-name', action='store', default='us-east-1',
    help='aws region name (default: us-east-1)')
  parser.add_argument('--stream-name',
    help='The name of the stream to put the data record into')
  parser.add_argument('--max-count', default=10, type=int,
    help='The max number of records to put (default: 10)')
  parser.add_argument('--console', action='store_true',
    help='Print out records ingested into the stream')
  parser.add_argument('--cdc-type', default='insert-only',
    choices=['insert-only', 'insert-update-or-delete'])
  parser.add_argument('--database', default='testdb',
    help='Database name')
  parser.add_argument('--table', default='retail_trans',
    help='Table name')
  parser.add_argument('--diskcache-dir', default='trans-cache-fztna',
    help='The disk cache directory (default: trans-cache-fztna)')
  parser.add_argument('--ttl-sec', default=3600,
    help='seconds until a cached item expires (default: 3600)')
  parser.add_argument('--dry-run', action='store_true')

  options = parser.parse_args()

  trans_cache = diskcache.Cache(options.diskcache_dir)
  main(options, trans_cache)

