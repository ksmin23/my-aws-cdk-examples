#!/usr/bin/env python3
import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_s3 as s3,
)

from constructs import Construct


class S3Stack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    self.artifact_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: core.RemovalPolicy.RETAIN - The bucket will be orphaned
      #XXX: create MLflow default S3 bucket name
      bucket_name=f"mlflow-sagemaker-{cdk.Aws.REGION}-{cdk.Aws.ACCOUNT_ID}")

    cdk.CfnOutput(self, 'MLflowArtifactBucketName',
      value=self.artifact_bucket.bucket_name,
      export_name=f'{self.stack_name}-MLflowArtifactBucketName')
