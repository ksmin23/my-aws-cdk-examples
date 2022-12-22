#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import argparse
import datetime
import json
import random
import time

import mimesis

# Mimesis 5.0 supports Python 3.8, 3.9, and 3.10.
# The Mimesis 4.1.3 is the last to support Python 3.6 and 3.7
# For more information, see https://mimesis.name/en/latest/changelog.html#version-5-0-0
assert mimesis.__version__ == '4.1.3'

from mimesis import locales
from mimesis.schema import Field, Schema

random.seed(47)


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--max-count', default=10, type=int, help='The max number of records to put.(default: 10)')

  options = parser.parse_args()

  CURRENT_YEAR = datetime.date.today().year
  start_year, end_year = (CURRENT_YEAR, CURRENT_YEAR)

  _ = Field(locale=locales.EN)
  _schema = Schema(schema=lambda: {
    "_id": _("uuid"),
    "clusterID": str(_("integer_number", start=1, end=50)),
    "connectionTime": _("formatted_datetime", fmt="%Y-%m-%d %H:%M:%S", start=start_year, end=end_year),
    "kWhDelivered": _("float_number", start=500.0, end=1500.0, precision=2),
    "stationID": _("integer_number", start=1, end=467),
    "spaceID": f'{_("word")}-{_("integer_number", start=1, end=20)}', # {{random.word}}-{{random.number({"min":1, "max":20})}
    "timezone": "America/Los_Angeles",
    "userID": str(_("integer_number", start=1000, end=500000)) # cast integer_number to string
  })

  cnt = 0
  for record in _schema.create(options.max_count):
    cnt += 1
    print(json.dumps(record))
    time.sleep(random.choices([0.01, 0.03, 0.05, 0.07, 0.1])[-1])

  print(f'[INFO] {cnt} records are processed', file=sys.stderr)


if __name__ == '__main__':
  main()

