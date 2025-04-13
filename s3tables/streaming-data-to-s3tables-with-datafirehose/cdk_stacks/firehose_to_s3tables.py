#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_kinesisfirehose
)
from constructs import Construct

from aws_cdk.aws_kinesisfirehose import CfnDeliveryStream as cfn_delivery_stream


class FirehoseToS3TablesStack(Stack):

  def __init__(self,
               scope: Construct,
               construct_id: str,
               s3_bucket,
               firehose_role,
               **kwargs) -> None:

    super().__init__(scope, construct_id, **kwargs)

    data_firehose_configuration = self.node.try_get_context("data_firehose_configuration")

    delivery_stream_name = data_firehose_configuration['stream_name']
    firehose_log_group_name = f"/aws/kinesisfirehose/{delivery_stream_name}"

    firehose_buffering_hints = data_firehose_configuration["buffering_hints"]
    firehose_buffer_size = firehose_buffering_hints["size_in_mbs"]
    firehose_buffer_interval = firehose_buffering_hints["interval_in_seconds"]

    s3_error_output_prefix = data_firehose_configuration["error_output_prefix"]

    dest_iceberg_table_config = data_firehose_configuration["destination_iceberg_table_configuration"]
    dest_iceberg_table_unique_keys = dest_iceberg_table_config.get("unique_keys", None)
    dest_iceberg_table_unique_keys = dest_iceberg_table_unique_keys if dest_iceberg_table_unique_keys else None

    iceberg_dest_config = cfn_delivery_stream.IcebergDestinationConfigurationProperty(
      catalog_configuration=cfn_delivery_stream.CatalogConfigurationProperty(
        catalog_arn=f"arn:aws:glue:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:catalog"
      ),
      role_arn=firehose_role.role_arn,
      s3_configuration=cfn_delivery_stream.S3DestinationConfigurationProperty(
        bucket_arn=s3_bucket.bucket_arn,
        role_arn=firehose_role.role_arn,
        buffering_hints={
          "intervalInSeconds": firehose_buffer_interval,
          "sizeInMBs": firehose_buffer_size
        },
        cloud_watch_logging_options={
          "enabled": True,
          "logGroupName": firehose_log_group_name,
          "logStreamName": "BackupDelivery"
        },
        compression_format="UNCOMPRESSED", # [GZIP | HADOOP_SNAPPY | Snappy | UNCOMPRESSED | ZIP]
        error_output_prefix=s3_error_output_prefix,
      ),
      buffering_hints={
        "intervalInSeconds": firehose_buffer_interval,
        "sizeInMBs": firehose_buffer_size
      },
      cloud_watch_logging_options={
        "enabled": True,
        "logGroupName": firehose_log_group_name,
        "logStreamName": "DestinationDelivery"
      },
      destination_table_configuration_list=[
        cfn_delivery_stream.DestinationTableConfigurationProperty(
          destination_database_name=dest_iceberg_table_config["database_name"],
          destination_table_name=dest_iceberg_table_config["table_name"],
          unique_keys=dest_iceberg_table_unique_keys
        )
      ],
      s3_backup_mode='FailedDataOnly'
    )

    delivery_stream = aws_kinesisfirehose.CfnDeliveryStream(self, "FirehoseToIceberg",
      delivery_stream_name=delivery_stream_name,
      delivery_stream_type="DirectPut",
      iceberg_destination_configuration=iceberg_dest_config,
      tags=[{"key": "Name", "value": delivery_stream_name}]
    )
    self.firehose_arn = delivery_stream.attr_arn


    cdk.CfnOutput(self, 'S3DestBucket',
      value=s3_bucket.bucket_name,
      export_name=f'{self.stack_name}-S3DestBucket')
    cdk.CfnOutput(self, 'DataFirehoseStreamName',
      value=delivery_stream.delivery_stream_name,
      export_name=f'{self.stack_name}-FirehoseStreamName')