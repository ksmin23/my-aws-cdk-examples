#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import argparse
import collections
import datetime
import random

import pandas as pd

from mimesis.locales import Locale
from mimesis.schema import Field, Schema

random.seed(47)

DEPARTMENTS = [
  'FC',
  'Finance',
  'IT',
  'Laws',
  'Manufacturing',
  'Marketing',
  'Purchasing',
  'R&D',
  'Sales',
  'Security'
]

COLUMNS_INFO = collections.OrderedDict([
  ('Op', 'N'),
  ('emp_no', 'KEY'),
  ('name', 'KEY'),
  ('department', 'U'),
  ('city', 'U'),
  ('salary', 'U'),
  ('m_time', 'N')
])

TODAY = datetime.date.today()


def gen_df(schema, n, time_col='m_time'):
  records = schema.create(iterations=n)
  res_df = pd.DataFrame.from_records(records)
  res_df[time_col] = res_df[time_col].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ'))
  return res_df


def gen_updated_cdc_df(sample_df, locale=Locale.EN):
  start_date = TODAY - datetime.timedelta(days=365*2)
  end_date = TODAY - datetime.timedelta(days=365*2)

  _ = Field(locale=locale)
  updated_schema = Schema(schema=lambda: {
    "Op": 'U',
    "department": _("choice", items=DEPARTMENTS),
    "city": _("city"),
    "salary": _("integer_number", start=50000, end=100000),
    "m_time": _("timestamp", posix=False, start=start_date.year, end=end_date.year)
  })

  num_samples = len(sample_df)
  updated_df = gen_df(updated_schema, num_samples)

  NON_UPDATABLE_COLUMNS = [k for k, v in COLUMNS_INFO.items() if v == 'KEY']
  old_df = sample_df[NON_UPDATABLE_COLUMNS].reset_index(drop=True)
  columns = [v for v in COLUMNS_INFO.keys()]
  res_df = pd.concat([updated_df, old_df], axis=1)[columns]
  return res_df


def gen_deleted_cdc_df(sample_df, locale=Locale.EN):
  start_date = TODAY - datetime.timedelta(days=365)
  end_date = TODAY - datetime.timedelta(days=365)

  _ = Field(locale=locale)
  deleted_schema = Schema(schema=lambda: {
    "Op": 'D',
    "m_time": _("timestamp", posix=False, start=start_date.year, end=end_date.year)
  })

  num_samples = len(sample_df)
  deleted_df = gen_df(deleted_schema, num_samples)

  NON_DELETED_COLUMNS = [k for k, v in COLUMNS_INFO.items() if v in ('KEY', 'U')]
  old_df = sample_df[NON_DELETED_COLUMNS].reset_index(drop=True)
  columns = [v for v in COLUMNS_INFO.keys()]
  res_df = pd.concat([deleted_df, old_df], axis=1)[columns]
  return res_df


def gen_inserted_cdc_df(insert_schema, n):
  res_df = gen_df(insert_schema, n)
  res_df['m_time'] = res_df['m_time'].apply(lambda x: x + datetime.timedelta(days=365*3))
  return res_df


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--type', default='FULL_LOAD_AND_CDC', choices=['FULL_LOAD', 'FULL_LOAD_AND_CDC'])
  parser.add_argument('--max-count', default=15, type=int, choices=range(10, 20), help='The max number of records to put. [10, 20)')
  parser.add_argument('--dry-run', action='store_true')

  options = parser.parse_args()

  start_date = TODAY - datetime.timedelta(days=365*4)
  end_date = TODAY - datetime.timedelta(days=365*3)

  _ = Field(locale=Locale.EN)
  insert_schema = Schema(schema=lambda: {
    "Op": 'I',
    "emp_no": _("increment", accumulator="emp_no"),
    "name": _("full_name"),
    "department": _("choice", items=DEPARTMENTS), 
    "city": _("city"),
    "salary": _("integer_number", start=1000, end=100000),
    "m_time": _("timestamp", posix=False, start=start_date.year, end=end_date.year)
  })

  full_load_df = gen_df(insert_schema, options.max_count)

  print('\n[full-load data]', file=sys.stderr)
  print(full_load_df, file=sys.stderr)
  if not options.dry_run:
    out_file = 'full-load-{}.parquet'.format(datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'))
    full_load_df.to_parquet(out_file, compression=None)

  if options.type == 'FULL_LOAD':
    return

  num_inserted_records = max(1, int(options.max_count*0.3))
  inserted_cdc_df = gen_inserted_cdc_df(insert_schema, num_inserted_records)

  updated_sample_df = full_load_df.sample(frac=0.5, random_state=23)
  updated_cdc_df = gen_updated_cdc_df(updated_sample_df, locale=Locale.EN)

  twice_updated_sample_df = updated_sample_df.sample(frac=0.3, random_state=37)
  twice_updated_cdc_df = gen_updated_cdc_df(twice_updated_sample_df, locale=Locale.EN)

  deleted_sample_df = updated_sample_df.sample(frac=0.2, random_state=47)
  deleted_cdc_df = gen_deleted_cdc_df(deleted_sample_df, locale=Locale.EN)

  cdc_df = pd.concat([inserted_cdc_df, deleted_cdc_df,
    updated_cdc_df, twice_updated_cdc_df]).sample(frac=1, random_state=47).sort_values(by=['m_time']).reset_index(drop=True)

  print('\n[cdc data]', file=sys.stderr)
  print(cdc_df, file=sys.stderr)
  if not options.dry_run:
    out_file = 'cdc-load-{}.parquet'.format(datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'))
    cdc_df.to_parquet(out_file, compression=None)


if __name__ == '__main__':
  main()
