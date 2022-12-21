#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import argparse
import datetime
import json
import random
import time

import boto3

from mimesis.locales import Locale
from mimesis.schema import Field, Schema

random.seed(47)


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--region-name', action='store', default='us-east-1',
    help='aws region name (default: us-east-1)')
  parser.add_argument('--stream-name', help='The name of the stream to put the data record into.')
  parser.add_argument('--max-count', default=10, type=int, help='The max number of records to put.')
  parser.add_argument('--dry-run', action='store_true')

  options = parser.parse_args()

  CURRENT_YEAR = datetime.date.today().year
  start_year, end_year = (CURRENT_YEAR, CURRENT_YEAR)

  _ = Field(locale=Locale.EN)
  _schema = Schema(schema=lambda: {
    "_id": _("uuid"),
    "clusterID": str(_("integer_number", start=1, end=50)),
    "connectionTime": _("formatted_datetime", fmt="%Y-%m-%d %H:%M:%S", start=start_year, end=end_year),
    "kWhDelivered": _("price"), # DECIMAL(10,2)
    "stationID": _("integer_number", start=1, end=467),
    "spaceID": f'{_("word")}-{_("integer_number", start=1, end=20)}', # {{random.word}}-{{random.number({"min":1, "max":20})}
    "timezone": "America/Los_Angeles",
    "userID": str(_("integer_number", start=1000, end=500000)) # cast integer_number to string
  })

  if not options.dry_run:
    kinesis_streams_client = boto3.client('kinesis', region_name=options.region_name)

  cnt = 0
  for record in _schema.iterator(options.max_count):
    cnt += 1

    if options.dry_run:
      print(json.dumps(record))
    else:
      res = kinesis_streams_client.put_record(
        StreamName=options.stream_name,
        Data=json.dumps(record),
        PartitionKey=record['_id']
      )

      if cnt % 100 == 0:
        print(f'[INFO] {cnt} records are processed', file=sys.stderr)

      if res['ResponseMetadata']['HTTPStatusCode'] != 200:
        print(res, file=sys.stderr)
    time.sleep(random.choices([0.01, 0.03, 0.05, 0.07, 0.1])[-1])
  print(f'[INFO] {cnt} records are processed', file=sys.stderr)


if __name__ == '__main__':
  main()

