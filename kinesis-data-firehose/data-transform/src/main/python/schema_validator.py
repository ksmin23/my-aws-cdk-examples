#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import base64
import json
import logging
import collections

import fastavro

LOGGER = logging.getLogger()
if len(LOGGER.handlers) > 0:
  # The Lambda environment pre-configures a handler logging to stderr.
  # If a handler is already configured, `.basicConfig` does not execute.
  # Thus we set the level directly.
  LOGGER.setLevel(logging.INFO)
else:
  logging.basicConfig(level=logging.INFO)


ORIGINAL_SCHEMA = {
  'name': 'Interactions',
  'type': 'record',
  'fields': [
    {
      'name': 'type',
      'type': {
        'name': 'EventType',
        'type': 'record',
        'fields':[
          {
            'name': 'device',
            'type': {
              'name': 'DeviceType',
              'type': 'enum',
              'symbols': ['pc', 'mobile', 'tablet']
            }
          },
          {
            'name': 'event',
            'type': 'string'
          }
        ]
      }
    },
    {
      'name': 'customer_id',
      'type': 'string'
    },
    {
      'name': 'event_timestamp',
      'type': 'long',
      'logicalType': 'timestamp-millis'
    },
    {
      'name': 'region',
      'type': ['string', 'null']
    }
  ]
}

PARSED_SCHEMA = fastavro.parse_schema(ORIGINAL_SCHEMA)

def check_schema(record):
  try:
    return fastavro.validation.validate(record, PARSED_SCHEMA, raise_errors=False)
  except Exception as ex:
    LOGGER.error(ex)
    return False

# Signature for all Lambda functions that user must implement
def lambda_handler(firehose_records_input, context):
  LOGGER.debug("Received records for processing from DeliveryStream: {deliveryStreamArn}, Region: {region}, and InvocationId: {invocationId}".format(
    deliveryStreamArn=firehose_records_input['deliveryStreamArn'],
    region=firehose_records_input['region'],
    invocationId=firehose_records_input['invocationId']))

  # Create return value.
  firehose_records_output = {'records': []}

  counter = collections.Counter(total=0, valid=0, invalid=0)

  # Create result object.
  # Go through records and process them
  for firehose_record_input in firehose_records_input['records']:
    counter['total'] += 1

    # Get user payload
    payload = base64.b64decode(firehose_record_input['data'])
    json_value = json.loads(payload)

    LOGGER.debug("Record that was received: {}".format(json_value))

    #TODO: check if schema is valid
    is_valid = check_schema(json_value)
    counter['valid' if is_valid else 'invalid'] += 1

    # Create output Firehose record and add modified payload and record ID to it.
    firehose_record_output = {
      'recordId': firehose_record_input['recordId'],
      #XXX: convert JSON to JSONLine
      'data': base64.b64encode(payload.rstrip(b'\n') + b'\n'),

      # The status of the data transformation of the record.
      # The possible values are: 
      #  Ok (the record was transformed successfully),
      #  Dropped (the record was dropped intentionally by your processing logic),
      # and ProcessingFailed (the record could not be transformed).
      # If a record has a status of Ok or Dropped, Kinesis Data Firehose considers it successfully processed.
      #  Otherwise, Kinesis Data Firehose considers it unsuccessfully processed.

      # 'ProcessFailed' record will be put into error bucket in S3
      'result': 'Ok' if is_valid else 'ProcessingFailed' # [Ok, Dropped, ProcessingFailed]
    }

    # Must set proper record ID
    # Add the record to the list of output records.
    firehose_records_output['records'].append(firehose_record_output)

  LOGGER.info(', '.join("{}={}".format(k, v) for k, v in counter.items()))

  # At the end return processed records
  return firehose_records_output


if __name__ == '__main__':
  import pprint

  record_list = [
    {
      "type": {
        "device": "mobile",
        "event": "visit"
      },
      "customer_id": "123456789012",
      "event_timestamp": 1633268355,
      "region": "ap-east-1"
    },
    {
      "type": {
        "device": "pc",
        "event": "view"
      },
      "customer_id": "123456789012",
      "event_timestamp": 1633268355,
      "region": "ap-east-1"
    },
    {
      "type": {
        "device": "tablet",
        "event": "purchase"
      },
      "customer_id": "123456789012",
      "event_timestamp": 1633268355,
      "region": "ap-east-1"
    },
    {
      "type": {
        "device": "mobile",
        "event": "list"
      },
      "customer_id": "123456789012",
      "event_timestamp": 1633268355
    },
    {
      "type": {
        "device": "mobile",
        "event": "list"
      },
      "customer_id": "123456789012",
      "event_timestamp": 1633268355,
      "region": None
    },
    {
      "type": {
        "device": "Andriod", # invalid 'device'
        "event": "purchase"
      },
      "customer_id": "123456789012",
      "event_timestamp": 1633268355,
      "region": "ap-east-1"
    },
    {
      "type": {
        "device": "mobile"
        # missing 'event'
      },
      "customer_id": "123456789012",
      "event_timestamp": 1633268355,
      "region": "ap-east-1"
    },
    {
      "type": {
        "device": "mobile",
        "event": "cart"
      },
      "customer_id": "123456789012",
      "event_timestamp": 1633268355.123, # invalid timestamp
      "region": "ap-east-1"
    },
    {
      # missing 'type'
      "customer_id": "123456789012",
      "event_timestamp": 1633268355,
      "region": "ap-east-1"
    },
    {
      "type": {
        "device": "mobile",
        "event": "list"
      },
      # missing 'customer_id'
      "event_timestamp": 1633268355,
      "region": "ap-east-1"
    },
    {
      "type": {
        "device": "mobile",
        "event": "list"
      },
      "customer_id": "123456789012",
      # missing 'event_timestamp'
      "region": "ap-east-1"
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

