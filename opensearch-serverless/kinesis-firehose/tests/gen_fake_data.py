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
    return random_datetime.strftime('%Y/%m/%d %H:%M:%S')


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--stream-name', help='Kinesis Data Firsehose Stream name')
  parser.add_argument('--region', default='us-east-1', help='Region name')
  parser.add_argument('--max-count', default=15, type=int, help='Number of messages to send, default is 15')
  parser.add_argument('--dry-run', action='store_true')

  options = parser.parse_args()

  _ = Field(locale=Locale.EN, providers=[CustomDatetime])
  schema = Schema(schema=lambda: {
    "userId": _("uuid"),
    "sessionId": _("token_hex", entropy=12),
    "referrer": _("internet.hostname"),
    "userAgent": _("internet.user_agent"),
    "ip": _("internet.ip_v4"),
    "hostname": _("internet.hostname"),
    "os": _("development.os"),
    "timestamp": _("custom_datetime.timestamp"),
    "uri": _("internet.uri", query_params_count=2)
  })

  if not options.dry_run:
    firehose = boto3.client('firehose', region_name=options.region)

  sent = 0
  for record in schema.iterator(options.max_count):
    msg = json.dumps(record)
    if options.dry_run:
      print(msg)
      continue

    firehose.put_record(
      DeliveryStreamName=options.stream_name,
      Record={
        'Data': msg
      }
    )
    sent += 1
    if sent % 100 == 0:
      print(f"{sent} sent", file=sys.stderr)
    time.sleep(0.5)

  if not options.dry_run:
    print(f"{sent} sent", file=sys.stderr)


if __name__ == '__main__':
  main()

