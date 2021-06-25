#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import argparse
import datetime
import json
import pprint
import random

import boto3

random.seed(47)


SAMPLE_RETAIL_TRANS = [
  {"Invoice": "489436", "StockCode": "22295", "Description": "HEART FILIGREE DOVE LARGE", "Quantity": 12, "InvoiceDate": "2021-06-25 23:06:00", "Price": 1.65, "Customer_ID": "13078.0", "Country": "United Kingdom"},
  {"Invoice": "489436", "StockCode": "22109", "Description": "FULL ENGLISH BREAKFAST PLATE", "Quantity": 16, "InvoiceDate": "2021-06-25 23:06:00", "Price": 3.39, "Customer_ID": "13078.0", "Country": "United Kingdom"},
  {"Invoice": "489436", "StockCode": "22107", "Description": "PIZZA PLATE IN BOX", "Quantity": 4, "InvoiceDate": "2021-06-25 23:06:00", "Price": 3.75, "Customer_ID": "13078.0", "Country": "United Kingdom"},
  {"Invoice": "489436", "StockCode": "22194", "Description": "BLACK DINER WALL CLOCK", "Quantity": 2, "InvoiceDate": "2021-06-25 23:06:00", "Price": 8.5, "Customer_ID": "13078.0", "Country": "United Kingdom"},
  {"Invoice": "489436", "StockCode": "35004B", "Description": "SET OF 3 BLACK FLYING DUCKS", "Quantity": 12, "InvoiceDate": "2021-06-25 23:06:00", "Price": 4.65, "Customer_ID": "13078.0", "Country": "United Kingdom"},
  {"Invoice": "489436", "StockCode": "82582", "Description": "AREA PATROLLED METAL SIGN", "Quantity": 12, "InvoiceDate": "2021-06-25 23:06:00", "Price": 2.1, "Customer_ID": "13078.0", "Country": "United Kingdom"},
  {"Invoice": "489436", "StockCode": "21181", "Description": "PLEASE ONE PERSON  METAL SIGN", "Quantity": 12, "InvoiceDate": "2021-06-25 23:06:00", "Price": 2.1, "Customer_ID": "13078.0", "Country": "United Kingdom"},
  {"Invoice": "489436", "StockCode": "21756", "Description": "BATH BUILDING BLOCK WORD", "Quantity": 3, "InvoiceDate": "2021-06-25 23:06:00", "Price": 5.95, "Customer_ID": "13078.0", "Country": "United Kingdom"},
  {"Invoice": "489436", "StockCode": "21333", "Description": "CLASSIC WHITE FRAME", "Quantity": 6, "InvoiceDate": "2021-06-25 23:06:00", "Price": 2.95, "Customer_ID": "13078.0", "Country": "United Kingdom"},
  {"Invoice": "489436", "StockCode": "84596F", "Description": "SMALL MARSHMALLOWS PINK BOWL", "Quantity": 8, "InvoiceDate": "2021-06-25 23:06:00", "Price": 1.25, "Customer_ID": "13078.0", "Country": "United Kingdom"},
]


def list_delivery_streams(client, stream_name):
  print("List Delivery Streams")
  response = client.list_delivery_streams(DeliveryStreamType="DirectPut")
  pprint.pprint(response["DeliveryStreamNames"])


def put_record_to_delivery_stream(client, stream_name, record):
  print("Put record to Delivery Stream")
  response = client.put_record(
    DeliveryStreamName=stream_name,
    Record={"Data": json.dumps(record, ensure_ascii=False)}
  )
  pprint.pprint(response)


def put_record_batch_to_delivery_stream(client, stream_name, record_list):
  print("Put records to Delivery Stream")
  records = [{"Data": json.dumps(elem, ensure_ascii=False)} for elem in record_list]
  response = client.put_record_batch(
    DeliveryStreamName=stream_name,
    Records=records
  )
  pprint.pprint(response)


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--region-name', action='store', default='us-east-1',
    help='aws region name (default: us-east-1)')
  parser.add_argument('--stream-name', help='The name of the stream to put the data record into.')
  parser.add_argument('--list-streams', action='store_true', help='List Kinesis Data Firehose streams.')
  parser.add_argument('--count', default=10, type=int, help='The max number of records to put. (1 <= count <= 10)')

  options = parser.parse_args()

  kinesis_firehose = boto3.client("firehose", region_name=options.region_name)

  if options.list_streams:
    list_delivery_streams(kinesis_firehose, options.stream_name)
    sys.exit(0)

  assert (options.count > 0)
  sample_size = min(options.count, len(SAMPLE_RETAIL_TRANS))
  sample_dataset = random.sample(SAMPLE_RETAIL_TRANS, k=sample_size)

  for elem in sample_dataset:
    elem['InvoiceDate'] = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

  if len(sample_dataset) == 1:
    put_record_to_delivery_stream(kinesis_firehose, options.stream_name, sample_dataset[0])
  else:
    put_record_batch_to_delivery_stream(kinesis_firehose, options.stream_name, sample_dataset)


if __name__ == "__main__":
  main()
