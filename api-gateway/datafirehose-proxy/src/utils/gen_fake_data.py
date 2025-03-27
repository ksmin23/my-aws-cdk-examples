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

from mimesis.locales import Locale
from mimesis.schema import Field, Schema
from mimesis.providers.base import BaseProvider
import requests


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

  parser.add_argument('--api-url', help='log collector api url')
  parser.add_argument('--api-method', default='records', choices=['record', 'records'],
    help='log collector api method [record | records]')
  parser.add_argument('--stream-name', help='kinesis stream name')
  parser.add_argument('--max-count', default=15, type=int, help='max number of records to put')
  parser.add_argument('--dry-run', action='store_true')

  options = parser.parse_args()

  _field = Field(locale=Locale.EN)
  _field._generic.add_provider(CustomDatetime)

  schema_definition = lambda: {
    "user_id": _field("uuid"),
    "session_id": _field("token_hex", entropy=12),
    "event": _field("choice", items=['visit', 'view', 'list', 'like', 'cart', 'purchase']),
    "referrer": _field("internet.hostname"),
    "user_agent": _field("internet.user_agent"),
    "ip": _field("internet.ip_v4"),
    "hostname": _field("internet.hostname"),
    "os": _field("development.os"),
    "timestamp": _field("custom_datetime.timestamp"),
    "uri": _field("internet.uri", query_params_count=2)
  }
  schema = Schema(schema=schema_definition, iterations=options.max_count)

  log_collector_url = f'{options.api_url}/streams/{options.stream_name}/{options.api_method}' if not options.dry_run else None

  for record in schema:
    if options.dry_run:
      print(json.dumps(record), file=sys.stderr)
      continue

    if options.api_method == 'record':
      data = {'Data': record}
      payload = f'{json.dumps(data)}'
    else:
      #XXX: make sure data has newline
      data = {"records":[{'data': f'{json.dumps(record)}\n'}]}
      payload = json.dumps(data)

    res = requests.put(log_collector_url, data=payload, headers={'Content-Type': 'application/json'})
    if res.status_code == 200:
      print(f'[{res.status_code} {res.reason}]', res.text, file=sys.stderr)
    else:
      print(f'[{res.status_code} {res.reason}]', file=sys.stderr)
      sys.exit(1)
    time.sleep(0.5)

if __name__ == '__main__':
  main()
