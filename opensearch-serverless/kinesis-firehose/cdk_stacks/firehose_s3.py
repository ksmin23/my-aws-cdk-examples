#!/usr/bin/env python3

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_s3 as s3,
)
from constructs import Construct

random.seed(47)


class KinesisFirehoseS3Stack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    S3_BUCKET_SUFFIX = ''.join(random.sample((string.ascii_lowercase + string.digits), k=7))
    s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: core.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name="firehose-to-ops-{region}-{suffix}".format(
        region=cdk.Aws.REGION, suffix=S3_BUCKET_SUFFIX))

    self.s3_bucket_name = s3_bucket.bucket_name
    self.s3_bucket_arn = s3_bucket.bucket_arn

    cdk.CfnOutput(self, f'{self.stack_name}-FirehoseS3DestBucketName', value=self.s3_bucket_name)
    cdk.CfnOutput(self, f'{self.stack_name}-FirehoseS3DestBucketArn', value=self.s3_bucket_arn)

