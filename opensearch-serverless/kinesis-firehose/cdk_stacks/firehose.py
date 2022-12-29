#!/usr/bin/env python3

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_s3 as s3,
  aws_kinesisfirehose
)
from constructs import Construct

random.seed(47)


class KinesisFirehoseStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, firehose_role_arn, opensearch_endpoint, s3_bucket_arn, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    FIREHOSE_DEFAULT_STREAM_NAME = 'PUT-AOS-{}'.format(''.join(random.sample((string.ascii_letters), k=5)))
    firehose_config = self.node.try_get_context('firehose')

    FIREHOSE_STREAM_NAME = firehose_config.get('stream_name', FIREHOSE_DEFAULT_STREAM_NAME)
    assert 1 <= len(FIREHOSE_STREAM_NAME) and len(FIREHOSE_STREAM_NAME) <= 64

    FIREHOSE_BUFFER_SIZE = firehose_config['buffer_size_in_mbs']
    assert 1 <= int(FIREHOSE_BUFFER_SIZE) and int(FIREHOSE_BUFFER_SIZE) <= 100

    FIREHOSE_BUFFER_INTERVAL = firehose_config['buffer_interval_in_seconds']
    assert 60 <= int(FIREHOSE_BUFFER_INTERVAL) and int(FIREHOSE_BUFFER_INTERVAL) <= 900

    OPENSEARCH_INDEX_NAME = firehose_config['opensearch_index_name']

    firehose_log_group_name = f"/aws/kinesisfirehose/{OPENSEARCH_INDEX_NAME}"

    opensearch_serverless_dest_config = aws_kinesisfirehose.CfnDeliveryStream.AmazonOpenSearchServerlessDestinationConfigurationProperty(
      index_name=OPENSEARCH_INDEX_NAME,
      role_arn=firehose_role_arn,
      s3_configuration={
        "bucketArn": s3_bucket_arn,
        "roleArn": firehose_role_arn,
        "bufferingHints": {
          "intervalInSeconds": FIREHOSE_BUFFER_INTERVAL,
          "sizeInMBs": FIREHOSE_BUFFER_SIZE
        },
        "cloudWatchLoggingOptions": {
          "enabled": True,
          "logGroupName": firehose_log_group_name,
          "logStreamName": "{OPENSEARCH_INDEX_NAME}-s3backup"
        },
        "compressionFormat": "UNCOMPRESSED", # [GZIP | HADOOP_SNAPPY | Snappy | UNCOMPRESSED | ZIP]
        # Kinesis Data Firehose automatically appends the “YYYY/MM/dd/HH/” UTC prefix to delivered S3 files. You can also specify
        # an extra prefix in front of the time format and add "/" to the end to have it appear as a folder in the S3 console.
        "errorOutputPrefix": "error/",
        "prefix": f"{OPENSEARCH_INDEX_NAME}/"
      },
      buffering_hints={
        "intervalInSeconds": FIREHOSE_BUFFER_INTERVAL,
        "sizeInMBs": FIREHOSE_BUFFER_SIZE
      },
      cloud_watch_logging_options={
        "enabled": True,
        "logGroupName": firehose_log_group_name,
        "logStreamName": "firehose-to-{OPENSEARCH_INDEX_NAME}"
      },
      collection_endpoint=opensearch_endpoint,
      retry_options={
        "durationInSeconds": 60
      },
      s3_backup_mode="AllDocuments", # [AllDocuments | FailedDocumentsOnly]
    )

    firehose_to_ops_serverless_delivery_stream = aws_kinesisfirehose.CfnDeliveryStream(self, "FirehoseToOpenSearchServerless",
      delivery_stream_name=FIREHOSE_STREAM_NAME,
      delivery_stream_type="DirectPut", # [DirectPut | KinesisStreamAsSource],
      amazon_open_search_serverless_destination_configuration=opensearch_serverless_dest_config,
      tags=[{"key": "Name", "value": OPENSEARCH_INDEX_NAME}]
    )

    cdk.CfnOutput(self, f'{self.stack_name}-S3DestBucketArn'.format(self.stack_name), value=s3_bucket_arn)
    cdk.CfnOutput(self, f'{self.stack_name}-FirehoseRoleArn', value=firehose_role_arn)

