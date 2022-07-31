#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import argparse
import collections
import datetime
import random

from faker import Faker
import pandas as pd

random.seed(47)

def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--type', default='FULL_LOAD_AND_CDC', choices=['FULL_LOAD', 'FULL_LOAD_AND_CDC'])
  parser.add_argument('--max-count', default=15, type=int, choices=range(1, 20), help='The max number of records to put. [1, 20)')
  parser.add_argument('--dry-run', action='store_true')

  options = parser.parse_args()

  fake = Faker()

  fake.set_arguments('append_only', {'elements': ['I']})
  fake.set_arguments('emp_no', {'digits': 3, 'fix_len': True})
  fake.set_arguments('department', {'elements': ['Finance', 'IT', 'Manufacturing', 'Purchasing', 'Sales']})
  fake.set_arguments('city', {'elements': ['Chicago', 'NY', 'Seoul', 'SFO', 'Tokyo']})
  fake.set_arguments('salary', {'digits': 5, 'fix_len': True})
  fake.set_arguments('end_mtime', {'end_datetime': datetime.date.today(), 'timespec': 'milliseconds'})

  DATA_COLUMNS = collections.OrderedDict([
    ('Op', 'random_element:append_only'),
    ('emp_no', 'random_number:emp_no'),
    ('name', 'first_name'),
    ('department', 'random_element:department'),
    ('city', 'random_element:city'),
    ('salary', 'random_number:salary'),
    ('m_time', 'iso8601:end_mtime')
  ])

  full_load_records = fake.json(data_columns=DATA_COLUMNS, num_rows=options.max_count)
  full_load_df = pd.read_json(full_load_records, orient='records')
  full_load_df = full_load_df.sort_values(by=['emp_no']).reset_index(drop=True)

  print('\n[full-load data]', file=sys.stderr)
  print(full_load_df, file=sys.stderr)
  if not options.dry_run:
    out_file = 'full-load-{}.parquet'.format(datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'))
    full_load_df.to_parquet(out_file, compression=None)

  if options.type == 'FULL_LOAD':
    return

  sample_df = full_load_df.sample(frac=0.3, random_state=47)
  num_samples = len(sample_df)

  new_mtime_list = []
  base_dt = datetime.datetime.utcnow() - datetime.timedelta(days=20)
  for _ in range(num_samples):
    base_dt += datetime.timedelta(hours=random.randint(1, 3), minutes=random.randint(1, 10))
    new_mtime_list.append(base_dt.isoformat(timespec='milliseconds'))

  fake.set_arguments('update_delete', {'elements': collections.OrderedDict([('U', 0.7), ('D', 0.3)])})
  fake.set_arguments('new_city', {'elements': ['Lisbon', 'Mumbai', 'Pargue', 'Seattle', 'Sydney', 'Taipei']})
  fake.set_arguments('new_department', {'elements': ['FC', 'Laws', 'Marketing', 'R&D', 'Security']})
  fake.set_arguments('new_mtime', {'elements': new_mtime_list})

  UPDATED_DATA_COLUMNS = {
    'Op': 'random_element:update_delete',
    'department': 'random_element:new_department',
    'city': 'random_element:new_city',
    'salary': 'random_number:salary',
    'm_time': 'random_element:new_mtime'
  }

  updated_or_deleted_records = fake.json(data_columns=UPDATED_DATA_COLUMNS, num_rows=num_samples)
  updated_or_deleted_df = pd.read_json(updated_or_deleted_records, orient='records')

  RENAME_COLUMNS = collections.OrderedDict([
    ('Op', 'Op'),
    ('emp_no', 'emp_no'),
    ('name', 'name'),
    ('department', 'department_2'),
    ('city', 'city_2'),
    ('salary', 'salary_2'),
    ('m_time', 'm_time')
  ])

  emp_details_df = sample_df[['emp_no', 'name', 'department', 'city', 'salary']].rename(columns=RENAME_COLUMNS).reset_index(drop=True)
  merged_cdc_df = pd.concat([updated_or_deleted_df, emp_details_df], axis=1)

  DELETED_REC_COLUMNS = [v for v in RENAME_COLUMNS.values()]
  deleted_cdc_df = merged_cdc_df[merged_cdc_df.Op == 'D'][DELETED_REC_COLUMNS].rename(columns={v: k for k, v in RENAME_COLUMNS.items()}).reset_index(drop=True)

  UPDATED_REC_COLUMNS = [v for v in RENAME_COLUMNS.keys()]
  updated_cdc_df = merged_cdc_df[merged_cdc_df.Op == 'U'][UPDATED_REC_COLUMNS].reset_index(drop=True)

  fake.set_arguments('new_emp_no', {'digits': 4, 'fix_len': True})

  DATA_COLUMNS['Op'] = 'random_element:append_only'
  DATA_COLUMNS['emp_no'] = 'random_number:new_emp_no'

  inserted_records = fake.json(data_columns=DATA_COLUMNS, num_rows=max(1, int(options.max_count*0.3)))
  inserted_df = pd.read_json(inserted_records, orient='records')
  cdc_df = pd.concat([deleted_cdc_df, updated_cdc_df, inserted_df]).sample(frac=1, random_state=47).reset_index(drop=True)

  print('\n[cdc data]', file=sys.stderr)
  print(cdc_df, file=sys.stderr)
  if not options.dry_run:
    out_file = 'cdc-load-{}.parquet'.format(datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'))
    cdc_df.to_parquet(out_file, compression=None)


if __name__ == '__main__':
  main()

