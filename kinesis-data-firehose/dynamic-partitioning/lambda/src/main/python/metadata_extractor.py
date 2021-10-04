#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import base64
import datetime
import json
import logging


LOGGER = logging.getLogger()
if len(LOGGER.handlers) > 0:
  # The Lambda environment pre-configures a handler logging to stderr.
  # If a handler is already configured, `.basicConfig` does not execute.
  # Thus we set the level directly.
  LOGGER.setLevel(logging.INFO)
else:
  logging.basicConfig(level=logging.INFO)


# Signature for all Lambda functions that user must implement
def lambda_handler(firehose_records_input, context):
  LOGGER.debug("Received records for processing from DeliveryStream: {deliveryStreamArn}, Region: {region}, and InvocationId: {invocationId}".format(
    deliveryStreamArn=firehose_records_input['deliveryStreamArn'],
    region=firehose_records_input['region'],
    invocationId=firehose_records_input['invocationId']))
 
  # Create return value.
  firehose_records_output = {'records': []}
 
  # Create result object.
  # Go through records and process them
  for firehose_record_input in firehose_records_input['records']:
    # Get user payload
    payload = base64.b64decode(firehose_record_input['data'])
    json_value = json.loads(payload)
 
    LOGGER.debug("Record that was received: {}".format(json_value))

    # Create output Firehose record and add modified payload and record ID to it.
    event_timestamp = datetime.datetime.fromtimestamp(json_value['event_timestamp'])
    partition_keys = {
      "region": json_value['region'],
      "device": json_value['type']['device'],
      "year": event_timestamp.strftime('%Y'),
      "month": event_timestamp.strftime('%m'),
      "day": event_timestamp.strftime('%d'),
      "hour": event_timestamp.strftime('%H')
    }
 
    # Create output Firehose record and add modified payload and record ID to it.
    firehose_record_output = {
      'recordId': firehose_record_input['recordId'],
      'data': firehose_record_input['data'],
      'result': 'Ok',
      'metadata': { 'partitionKeys': partition_keys }
    }
 
    # Must set proper record ID
    # Add the record to the list of output records.
    firehose_records_output['records'].append(firehose_record_output)
 
  # At the end return processed records
  return firehose_records_output


if __name__ == '__main__':
  import pprint

  record = {"type": {"device": "mobile", "event": "list"}, "customer_id": "123456789012", "event_timestamp": 1633268355, "region": "ap-east-1"}

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


