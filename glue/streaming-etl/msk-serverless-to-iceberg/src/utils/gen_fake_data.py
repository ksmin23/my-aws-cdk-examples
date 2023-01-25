#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import argparse
from datetime import datetime
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

  _CURRENT_YEAR = datetime.now().year
  _NAMES = 'Arica,Burton,Cory,Fernando,Gonzalo,Kenton,Linsey,Micheal,Ricky,Takisha'.split(',')

  #XXX: For more information about synthetic data schema, see
  # https://github.com/aws-samples/aws-glue-streaming-etl-blog/blob/master/config/generate_data.py
  _ = Field(locale=locales.EN)

  _schema = Schema(schema=lambda: {
    # "name": _("first_name"),
    "name": _("choice", items=_NAMES),
    "age": _("age"),
    "m_time": _("formatted_datetime", fmt="%Y-%m-%d %H:%M:%S", start=_CURRENT_YEAR, end=_CURRENT_YEAR)
  })

  cnt = 0
  for record in _schema.create(options.max_count):
    cnt += 1
    partition_key = record['name']
    print(f"{partition_key}\t{json.dumps(record)}")
    time.sleep(random.choices([0.01, 0.03, 0.05, 0.07, 0.1])[-1])

  print(f'[INFO] {cnt} records are processed', file=sys.stderr)


if __name__ == '__main__':
  main()

