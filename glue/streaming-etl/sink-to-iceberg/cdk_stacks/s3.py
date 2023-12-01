#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

from urllib.parse import urlparse

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_s3 as s3
)

from constructs import Construct


class S3BucketStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    glue_job_input_arguments = self.node.try_get_context('glue_job_input_arguments')
    s3_path = glue_job_input_arguments["--iceberg_s3_path"]
    s3_bucket_name = urlparse(s3_path).netloc

    s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: cdk.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name=s3_bucket_name)

    self.s3_bucket_name = s3_bucket.bucket_name

    cdk.CfnOutput(self, f'{self.stack_name}_S3Bucket', value=self.s3_bucket_name)
