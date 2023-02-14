#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import argparse
import json
import random
import time
import datetime

import boto3
from mimesis.locales import Locale
from mimesis.schema import Field, Schema
from mimesis.providers.base import BaseProvider


class CustomDatetimeProvider(BaseProvider):
  class Meta:
    """Class for metadata."""
    name = "custom_datetime"

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


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--region-name', action='store', default='us-east-1',
    help='aws region name (default: us-east-1)')
  parser.add_argument('--stream-name', help='The name of the stream to put the data record into')
  parser.add_argument('--max-count', default=10, type=int, help='The max number of records to put (default: 10)')
  parser.add_argument('--dry-run', action='store_true')
  parser.add_argument('--console', action='store_true', help='Print out records ingested into the stream')

  options = parser.parse_args()

  _ = Field(locale=Locale.EN, providers=[CustomDatetimeProvider])

  manufacturers = [
    "Mazda",
    "Lancia",
    "Peugeot",
    "Maybach",
    "Chevrolet",
    "Mercedes-Benz",
    "Nissan",
    "Volkswagen",
    "Fiat",
    "Daihatsu"
  ]

  _schema = Schema(schema=lambda: {
    "product_id": f'{_("integer_number", start=1, end=20):05}',
    "product_name": _("car"),
    "price": _("integer_number", start=1000, end=12345),
    "category": _("choice", items=manufacturers),
    "updated_at": _("custom_datetime.formated_datetime", fmt="%Y-%m-%d %H:%M:%S", lt_now=True),
  })

  if not options.dry_run:
    kinesis_streams_client = boto3.client('kinesis', region_name=options.region_name)

  cnt = 0
  for record in _schema.iterator(options.max_count):
    cnt += 1

    if options.dry_run:
      print(f"{json.dumps(record)}")
    else:
      res = kinesis_streams_client.put_record(
        StreamName=options.stream_name,
        Data=f"{json.dumps(record)}\n", # convert JSON to JSON Line
        PartitionKey=f"{record['product_id']}"
      )

      if options.console:
        print(f"{json.dumps(record)}")

      if cnt % 100 == 0:
        print(f'[INFO] {cnt} records are processed', file=sys.stderr)

      if res['ResponseMetadata']['HTTPStatusCode'] != 200:
        print(res, file=sys.stderr)
    time.sleep(random.choices([0.01, 0.03, 0.05, 0.07, 0.1])[-1])
  print(f'[INFO] Total {cnt} records are processed', file=sys.stderr)


if __name__ == '__main__':
  main()
