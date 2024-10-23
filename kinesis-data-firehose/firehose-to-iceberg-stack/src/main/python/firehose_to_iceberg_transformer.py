#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import base64
import json
import os

DESTINATION_DATABASE_NAME = os.environ['IcebergeDatabaseName']
DESTINATION_TABLE_NAME = os.environ['IcebergTableName']


def lambda_handler(event, context):
  firehose_records_output = {'records': []}

  for record in event['records']:
    payload = base64.b64decode(record['data']).decode('utf-8')
    json_value = json.loads(payload)

    data = json.dumps(json_value['data'])
    metadata = json_value['metadata']
    operation = metadata['operation']

    if operation not in ('insert', 'update', 'delete'):
      continue

    firehose_record = {
      'data': base64.b64encode(data.encode('utf-8')),
      'recordId': record['recordId'],
      'result': 'Ok',
      'metadata': {
        'otfMetadata': {
          'destinationDatabaseName': DESTINATION_DATABASE_NAME,
          'destinationTableName': DESTINATION_TABLE_NAME,
          'operation': operation
        }
      }
    }

    firehose_records_output['records'].append(firehose_record)

  return firehose_records_output


if __name__ == '__main__':
  import pprint

  record_list = [
    {
      "data": {
        "trans_id": 6,
        "customer_id": "387378799012",
        "event": "list",
        "sku": "AI6161BEFX",
        "amount": 1,
        "device": "pc",
        "trans_datetime": "2023-01-16T06:18:32Z"
      },
      "metadata": {
        "timestamp": "2023-01-16T06:25:34.444953Z",
        "record-type": "data",
        "operation": "insert",
        "partition-key-type": "primary-key",
        "schema-name": "testdb",
        "table-name": "retail_trans",
        "transaction-id": 12884904641
      }
    },
    {
      "data": {
        "trans_id": 6,
        "customer_id": "387378799012",
        "event": "list",
        "sku": "AI6161BEFX",
        "amount": 3,
        "device": "pc",
        "trans_datetime": "2023-01-16T06:18:32Z"
      },
      "metadata": {
        "timestamp": "2023-01-16T08:05:25.942777Z",
        "record-type": "data",
        "operation": "update",
        "partition-key-type": "primary-key",
        "schema-name": "testdb",
        "table-name": "retail_trans",
        "transaction-id": 12884973957
      }
    },
    {
      "data": {
        "trans_id": 6,
        "customer_id": "387378799012",
        "event": "list",
        "sku": "AI6161BEFX",
        "amount": 3,
        "device": "pc",
        "trans_datetime": "2023-01-16T06:18:32Z"
      },
      "metadata": {
        "timestamp": "2023-01-16T08:10:49.737891Z",
        "record-type": "data",
        "operation": "delete",
        "partition-key-type": "primary-key",
        "schema-name": "testdb",
        "table-name": "retail_trans",
        "transaction-id": 12884978099
      }
    }
  ]

  for record in record_list:
    event = {
      "invocationId": "invocationIdExample",
      "deliveryStreamArn": "arn:aws:kinesis:EXAMPLE",
      "region": "us-east-1",
      "records": [
        {
          "recordId": "49546986683135544286507457936321625675700192471156785154",
          "approximateArrivalTimestamp": 1495072949453,
          "data": base64.b64encode(json.dumps(record).encode('utf-8'))
        }
      ]
    }

    res = lambda_handler(event, {})
    pprint.pprint(res)
