#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_s3 as s3
)

from constructs import Construct


class S3BucketStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    S3_DEFAULT_BUCKET_NAME = f"firehose-s3tables-{cdk.Aws.REGION}-{cdk.Aws.ACCOUNT_ID}"
    firehose_config = self.node.try_get_context("data_firehose_configuration")
    s3_bucket_name = firehose_config.get('s3_bucket', S3_DEFAULT_BUCKET_NAME)
    self.s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: core.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name=s3_bucket_name)

    cdk.CfnOutput(self, 'S3BucketName',
      value=self.s3_bucket.bucket_name,
      export_name=f'{self.stack_name}-S3BucketName')