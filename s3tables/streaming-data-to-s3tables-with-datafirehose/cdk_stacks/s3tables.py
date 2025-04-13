#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_s3tables,
)

from constructs import Construct


class S3TablesStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    S3TABLE_DEFAULT_BUCKET_NAME = f"s3tables-{cdk.Aws.REGION}-{cdk.Aws.ACCOUNT_ID}"
    s3tables_config = self.node.try_get_context("s3_tables")
    s3table_bucket_name = s3tables_config.get('table_bucket_name', S3TABLE_DEFAULT_BUCKET_NAME)

    self.s3table_bucket = aws_s3tables.CfnTableBucket(self, "CfnS3TableBucket",
      table_bucket_name=s3table_bucket_name,

      # (Optional) The unreferenced file removal settings for your table bucket.
      # For more information, see
      # https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-table-buckets-maintenance.html
      unreferenced_file_removal=aws_s3tables.CfnTableBucket.UnreferencedFileRemovalProperty(
        noncurrent_days=10, # default=10
        status="Enabled",
        unreferenced_days=3 # default=3
      )
    )

    self.table_bucket_name = self.s3table_bucket.table_bucket_name


    cdk.CfnOutput(self, 'S3TableBucketArn',
      value=self.s3table_bucket.attr_table_bucket_arn,
      export_name=f'{self.stack_name}-S3TableBucketArn')
    cdk.CfnOutput(self, 'S3TableBucketName',
      value=self.table_bucket_name,
      export_name=f'{self.stack_name}-S3TableBucketName')