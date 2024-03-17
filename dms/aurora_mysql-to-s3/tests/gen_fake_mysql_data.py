#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import argparse
import datetime
import itertools
import json
import sys
import string
import time

import boto3
from faker import Faker
import pymysql
import dataset

Faker.seed(47)

CREATE_TABLE_SQL_FMT = '''
CREATE TABLE IF NOT EXISTS {database}.{table} (
  trans_id BIGINT(20) AUTO_INCREMENT PRIMARY KEY,
  customer_id VARCHAR(12) NOT NULL,
  event VARCHAR(10) DEFAULT NULL,
  sku VARCHAR(10) NOT NULL,
  amount INT DEFAULT 0,
  device VARCHAR(10) DEFAULT NULL,
  trans_datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY(trans_datetime)
) ENGINE=InnoDB AUTO_INCREMENT=0;
'''

DROP_TABLE_SQL_FMT = '''DROP TABLE IF NOT EXISTS {database}.{table};'''

INSERT_SQL_FMT = '''INSERT INTO {database}.{table} (customer_id, event, sku, amount, device, trans_datetime) VALUES("{customer_id}", "{event}", "{sku}", {amount}, "{device}", "{trans_datetime}");'''

DB_URL_FMT = 'mysql+pymysql://{user}:{password}@{host}?autocommit=True'

def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--region-name', action='store', default='us-east-1',
    help='aws region name (default: us-east-1)')
  parser.add_argument('--host', action='store', help='database host')
  parser.add_argument('-u', '--user', action='store', help='user name')
  parser.add_argument('-p', '--password', action='store', help='password')
  parser.add_argument('--database', action='store', default='testdb',
    help='database name (default: testdb)')
  parser.add_argument('--table', action='store', default='retail_trans',
    help='table name (default: retail_trans)')
  parser.add_argument('--max-count', default=10, type=int, help='The max number of records to put.')
  parser.add_argument('--dry-run', action='store_true')
  parser.add_argument('--create-table', action='store_true')
  parser.add_argument('--drop-table', action='store_true')

  options = parser.parse_args()

  fake = Faker()

  db_url = DB_URL_FMT.format(user=options.user, password=options.password, host=options.host)
  if not options.dry_run:
    db = dataset.connect(db_url)

  if options.create_table:
    sql_stmt = CREATE_TABLE_SQL_FMT.format(database=options.database, table=options.table)
    print(sql_stmt)
    if not options.dry_run:
      db.query(sql_stmt)
    return

  if options.drop_table:
    sql_stmt = DROP_TABLE_SQL_FMT.format(database=options.database, table=options.table)
    print(sql_stmt)
    if not options.dry_run:
      db.query(sql_stmt)
    return

  START_DATETIME = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
  predicate = (lambda x: x < options.max_count) if options.max_count >= 0 else (lambda x: x > options.max_count)
  for cnt in itertools.takewhile(predicate, itertools.count()):
    event = fake.random_element(elements=['visit', 'view', 'cart', 'list', 'like', 'purchase'])
    amount = fake.pyint(max_value=100) if event in ['cart', 'purchase'] else 1
    json_record = {
      'device': fake.random_element(elements=['pc', 'mobile', 'tablet']),
      'event': event,
      'sku': fake.pystr_format(string_format='??%###????', letters=string.ascii_uppercase),
      'amount': amount,
      'customer_id': fake.pystr_format(string_format='%###########'),
      'trans_datetime': fake.date_time_ad(start_datetime=START_DATETIME).strftime('%Y-%m-%d %H:%M:%S')
    }
    record = json.dumps(json_record)
    sql_stmt = INSERT_SQL_FMT.format(database=options.database, table=options.table, **json_record)

    if options.dry_run:
      print(record, file=sys.stderr)
    else:
      db.query(sql_stmt)

      if (cnt + 1) % 100 == 0:
        print(sql_stmt)
        print('[INFO] {} records are processed'.format(cnt+1), file=sys.stderr)
    time.sleep(3)

  print('[INFO] Total {} records are processed'.format(cnt+1), file=sys.stderr)


if __name__ == '__main__':
  main()
