#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import argparse
import json
import random
import time

import boto3


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--region-name', action='store', default='us-east-1',
    help='aws region name (default: us-east-1)')
  parser.add_argument('--stream-name', help='The name of the stream to put the data record into')
  parser.add_argument('--dry-run', action='store_true')
  parser.add_argument('--console', action='store_true', help='Print out records ingested into the stream')
  parser.add_argument('--cdc-type', choices=['insert-only', 'insert-update-or-delete'])

  options = parser.parse_args()

  insert_only_cdc_list = [
    # Insert
    {"data": {"trans_id": 6, "customer_id": "387378799012", "event": "list", "sku": "AI6161BEFX", "amount": 1, "device": "pc", "trans_datetime": "2023-01-16T06:18:32Z"}, "metadata": {"timestamp": "2023-01-16T06:25:34.444953Z", "record-type": "data", "operation": "insert", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884904641}},
    {"data": {"trans_id": 19, "customer_id": "826787813308", "event": "visit", "sku": "DK2617NXBK", "amount": 1, "device": "tablet", "trans_datetime": "2023-01-16T06:11:06Z"}, "metadata": {"timestamp": "2023-01-16T06:26:14.899137Z", "record-type": "data", "operation": "insert", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884909253}},
    {"data": {"trans_id": 21, "customer_id": "997346006365", "event": "cart", "sku": "NL7461YPIB", "amount": 77, "device": "tablet", "trans_datetime": "2023-01-16T06:03:01Z"}, "metadata": {"timestamp": "2023-01-16T06:26:19.942369Z", "record-type": "data", "operation": "insert", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884909966}},
    {"data": {"trans_id": 23, "customer_id": "110409389008", "event": "cart", "sku": "KZ7560ZRLA", "amount": 60, "device": "pc", "trans_datetime": "2023-01-16T06:13:05Z"}, "metadata": {"timestamp": "2023-01-16T06:26:25.001169Z", "record-type": "data", "operation": "insert", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884910678}},
    {"data": {"trans_id": 24, "customer_id": "240977651465", "event": "list", "sku": "LB9146CJTW", "amount": 1, "device": "pc", "trans_datetime": "2023-01-16T06:24:10Z"}, "metadata": {"timestamp": "2023-01-16T06:26:30.146196Z", "record-type": "data", "operation": "insert", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884911030}},
    {"data": {"trans_id": 27, "customer_id": "877946792067", "event": "like", "sku": "EJ2923TPZU", "amount": 1, "device": "tablet", "trans_datetime": "2023-01-16T06:24:59Z"}, "metadata": {"timestamp": "2023-01-16T06:26:35.233576Z", "record-type": "data", "operation": "insert", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884912098}},
    {"data": {"trans_id": 28, "customer_id": "342761190559", "event": "list", "sku": "MM5584BTYQ", "amount": 1, "device": "mobile", "trans_datetime": "2023-01-16T06:00:02Z"}, "metadata": {"timestamp": "2023-01-16T06:26:40.280210Z", "record-type": "data", "operation": "insert", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884912454}},
    {"data": {"trans_id": 30, "customer_id": "783305627923", "event": "cart", "sku": "SZ9293QYKU", "amount": 14, "device": "pc", "trans_datetime": "2023-01-16T06:24:51Z"}, "metadata": {"timestamp": "2023-01-16T06:26:45.381542Z", "record-type": "data", "operation": "insert", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884913162}},
    {"data": {"trans_id": 33, "customer_id": "992164363133", "event": "cart", "sku": "CM8337UAUY", "amount": 78, "device": "tablet", "trans_datetime": "2023-01-16T06:03:02Z"}, "metadata": {"timestamp": "2023-01-16T06:26:55.484725Z", "record-type": "data", "operation": "insert", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884914226}},
    {"data": {"trans_id": 35, "customer_id": "168395939233", "event": "like", "sku": "HQ9147QPJK", "amount": 1, "device": "pc", "trans_datetime": "2023-01-16T06:01:00Z"}, "metadata": {"timestamp": "2023-01-16T06:27:00.589359Z", "record-type": "data", "operation": "insert", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884914938}},
  ]

  dml_cdc_list = [
    # Update
    {"data": {"trans_id": 19, "customer_id": "826787813308", "event": "visit", "sku": "DK2617NXBK", "amount": 39, "device": "tablet", "trans_datetime": "2023-01-16T06:11:06Z"}, "metadata": {"timestamp": "2023-01-16T08:05:36.061467Z", "record-type": "data", "operation": "update", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884974367}},
    {"data": {"trans_id": 21, "customer_id": "997346006365", "event": "cart", "sku": "NL7461YPIB", "amount": 60, "device": "tablet", "trans_datetime": "2023-01-16T06:03:01Z"}, "metadata": {"timestamp": "2023-01-16T08:05:46.158075Z", "record-type": "data", "operation": "update", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884974787}},
    {"data": {"trans_id": 24, "customer_id": "240977651465", "event": "list", "sku": "LB9146CJTW", "amount": 42, "device": "pc", "trans_datetime": "2023-01-16T06:24:10Z"}, "metadata": {"timestamp": "2023-01-16T08:06:21.584627Z", "record-type": "data", "operation": "update", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884975615}},
    {"data": {"trans_id": 30, "customer_id": "783305627923", "event": "cart", "sku": "SZ9293QYKU", "amount": 67, "device": "pc", "trans_datetime": "2023-01-16T06:24:51Z"}, "metadata": {"timestamp": "2023-01-16T08:06:41.807706Z", "record-type": "data", "operation": "update", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884976861}},
    {"data": {"trans_id": 35, "customer_id": "168395939233", "event": "like", "sku": "HQ9147QPJK", "amount": 85, "device": "pc", "trans_datetime": "2023-01-16T06:01:00Z"}, "metadata": {"timestamp": "2023-01-16T08:07:02.085752Z", "record-type": "data", "operation": "update", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884977689}},

    # Delete
    {"data": {"trans_id": 6, "customer_id": "387378799012", "event": "list", "sku": "AI6161BEFX", "amount": 3, "device": "pc", "trans_datetime": "2023-01-16T06:18:32Z"}, "metadata": {"timestamp": "2023-01-16T08:10:49.737891Z", "record-type": "data", "operation": "delete", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884978099}},
    {"data": {"trans_id": 33, "customer_id": "992164363133", "event": "cart", "sku": "CM8337UAUY", "amount": 34, "device": "tablet", "trans_datetime": "2023-01-16T06:03:02Z"}, "metadata": {"timestamp": "2023-01-16T08:11:15.067609Z", "record-type": "data", "operation": "delete", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884978449}},
    {"data": {"trans_id": 23, "customer_id": "110409389008", "event": "cart", "sku": "KZ7560ZRLA", "amount": 4, "device": "pc", "trans_datetime": "2023-01-16T06:13:05Z"}, "metadata": {"timestamp": "2023-01-16T08:13:16.515265Z", "record-type": "data", "operation": "delete", "partition-key-type": "primary-key", "schema-name": "testdb", "table-name": "retail_trans", "transaction-id": 12884978803}},

    # Insert
    {"data":{"trans_id":37, "customer_id": "818177069814", "event": "like", "sku": "JS6166YPTE", "amount": 1, "device": "mobile", "trans_datetime": "2023-01-16T08:08:44Z"}, "metadata":{"timestamp":"2023-01-16T08:08:16.515265Z", "record-type":"data", "operation":"insert", "partition-key-type":"primary-key", "schema-name":"testdb", "table-name": "retail_trans", "transaction-id": 12884978815}},
    {"data":{"trans_id":38, "customer_id": "387378799012", "event": "list", "sku": "AI6161BEFX", "amount": 1, "device": "pc", "trans_datetime": "2023-01-16T08:09:33Z"}, "metadata":{"timestamp":"2023-01-16T08:10:15.067609Z", "record-type":"data", "operation":"insert", "partition-key-type": "primary-key", "schema-name":"testdb", "table-name": "retail_trans", "transaction-id": 12884978849}},
    {"data":{"trans_id":41, "customer_id": "839828949919", "event": "purchase", "sku": "AC2306JBRJ", "amount": 5, "device": "tablet", "trans_datetime": "2023-01-16T08:14:20Z"}, "metadata":{"timestamp":"2023-01-16T08:14:41.807706Z", "record-type":"data", "operation":"insert", "partition-key-type":"primary-key", "schema-name": "testdb", "table-name":" retail_trans", "transaction-id": 12884978861}},
    {"data":{"trans_id":43, "customer_id": "248083404876", "event": "visit", "sku": "AS8552DVOO", "amount": 1, "device": "pc", "trans_datetime": "2023-01-16T08:21:05Z"}, "metadata":{"timestamp":"2023-01-16T08:21:32.085752Z", "record-type":"data", "operation":"insert", "partition-key-type":"primary-key", "schema-name":"testdb", "table-name": "retail_trans", "transaction-id": 12884978889}},
    {"data":{"trans_id":47, "customer_id": "731184658511", "event": "like", "sku": "XZ9997LSJN", "amount": 1, "device": "tablet", "trans_datetime": "2023-01-16T08:33:47Z"}, "metadata":{"timestamp":"2023-01-16T29:10:49.737891Z", "record-type":"data", "operation":"insert", "partition-key-type":"primary-key", "schema-name":"testdb", "table-name": "retail_trans", "transaction-id": 12884978897}},
  ]

  if not options.dry_run:
    firehose_client = boto3.client('firehose', region_name=options.region_name)

  cdc_list = insert_only_cdc_list if options.cdc_type == 'insert-only' else dml_cdc_list

  for cnt, record in enumerate(cdc_list):
    record = json.dumps(record)

    if options.dry_run:
      print(f"{record}")
    else:
      res = firehose_client.put_record(
        DeliveryStreamName=options.stream_name,
        Record={
          'Data': record
        }
      )

      if options.console:
        print(f"{record}")

      if (cnt+1) % 100 == 0:
        print(f'[INFO] {cnt+1} records are processed', file=sys.stderr)

      if res['ResponseMetadata']['HTTPStatusCode'] != 200:
        print(res, file=sys.stderr)
      time.sleep(random.choices([0.01, 0.03, 0.05, 0.07, 0.1])[-1])
  print(f'[INFO] Total {cnt+1} records are processed', file=sys.stderr)


if __name__ == '__main__':
  main()