#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import argparse
from datetime import (
  datetime,
  timezone
)
import json
import time
import typing

import boto3
from mimesis.locales import Locale
from mimesis.schema import Field, Schema
from mimesis.providers.base import BaseProvider


class CustomDatetime(BaseProvider):
  class Meta:
    """Class for metadata."""
    name: typing.Final[str] = "custom_datetime"

  def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
    super().__init__(*args, **kwargs)

  def timestamp(self) -> str:
    utc_now = datetime.now(timezone.utc)
    minute = self.random.randint(0, 59)
    second = self.random.randint(0, 59)
    random_datetime = utc_now.replace(minute=minute, second=second)
    return random_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--region-name', action='store', default='us-east-1',
    help='aws region name (default: us-east-1)')
  parser.add_argument('--stream-name', help='kinesis stream name')
  parser.add_argument('--max-count', default=15, type=int, help='max number of records to put')
  parser.add_argument('--dry-run', action='store_true')
  parser.add_argument('--console', action='store_true', help='Print out records ingested into the stream')

  options = parser.parse_args()

  _field = Field(locale=Locale.EN)
  _field._generic.add_provider(CustomDatetime)

  schema_definition = lambda: {
    "id": _field("numeric.increment", accumulator="pkid"),
    "name": _field("person.username"),
    "value": _field("numeric.integer_number", start=0)
  }
  schema = Schema(schema=schema_definition, iterations=options.max_count)

  if not options.dry_run:
    firehose_client = boto3.client('firehose', region_name=options.region_name)

  for cnt, row in enumerate(schema):
    record = json.dumps(row)

    if options.dry_run:
      print(record, file=sys.stderr)
    else:
      res = firehose_client.put_record(
        DeliveryStreamName=options.stream_name,
        Record={
          'Data': record
        }
      )

      if res['ResponseMetadata']['HTTPStatusCode'] != 200:
        print(res, file=sys.stderr)
      time.sleep(0.5)

    if options.console:
      print(f"{record}")

    if (cnt+1) % 100 == 0:
      print(f'[INFO] {cnt+1} records are processed', file=sys.stderr)
  print(f'[INFO] Total {cnt+1} records are processed', file=sys.stderr)


if __name__ == '__main__':
  main()