#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_s3 as s3,
)
from constructs import Construct

random.seed(47)

class S3Stack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    S3_BUCKET_SUFFIX = ''.join(random.sample((string.ascii_lowercase + string.digits), k=7))
    self.s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.RETAIN, #XXX: Default: cdk.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name=f"msk-serverless-firehose-s3-{cdk.Aws.REGION}-{S3_BUCKET_SUFFIX}")

    cdk.CfnOutput(self, 'S3BucketArn', value=self.s3_bucket.bucket_arn,
      export_name=f'{self.stack_name}-S3BucketArn')
    cdk.CfnOutput(self, 'S3BucketName', value=self.s3_bucket.bucket_name,
      export_name=f'{self.stack_name}-S3BucketName')
