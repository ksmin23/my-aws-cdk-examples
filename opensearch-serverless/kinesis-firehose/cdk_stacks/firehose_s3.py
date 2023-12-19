#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_s3 as s3,
)
from constructs import Construct


class KinesisFirehoseS3Stack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: core.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name=f"firehose-to-ops-{cdk.Aws.REGION}-{self.stack_name.lower()}")

    self.s3_bucket_name = s3_bucket.bucket_name
    self.s3_bucket_arn = s3_bucket.bucket_arn

    cdk.CfnOutput(self, 'FirehoseS3DestBucketName',
      value=self.s3_bucket_name,
      export_name=f'{self.stack_name}-FirehoseS3DestBucketName')
    cdk.CfnOutput(self, 'FirehoseS3DestBucketArn',
      value=self.s3_bucket_arn,
      export_name=f'{self.stack_name}-FirehoseS3DestBucketArn')

