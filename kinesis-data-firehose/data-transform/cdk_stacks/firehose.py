#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam,
  aws_s3 as s3,
  aws_kinesisfirehose
)
from constructs import Construct

from aws_cdk.aws_kinesisfirehose import CfnDeliveryStream as cfn

random.seed(31)

class KinesisFirehoseStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, data_transform_lambda_fn, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    S3_BUCKET_SUFFIX = ''.join(random.sample((string.ascii_lowercase + string.digits), k=7))
    s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: core.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name="firehose-to-s3-{region}-{suffix}".format(
        region=cdk.Aws.REGION, suffix=S3_BUCKET_SUFFIX))

    FIREHOSE_STREAM_NAME = cdk.CfnParameter(self, 'FirehoseStreamName',
      type='String',
      description='kinesis data firehose stream name',
      default='PUT-S3-{}'.format(''.join(random.sample((string.ascii_letters), k=5)))
    )

    FIREHOSE_BUFFER_SIZE = cdk.CfnParameter(self, 'FirehoseBufferSize',
      type='Number',
      description='kinesis data firehose buffer size',
      min_value=1,
      max_value=128,
      default=128
    )

    FIREHOSE_BUFFER_INTERVAL = cdk.CfnParameter(self, 'FirehoseBufferInterval',
      type='Number',
      description='kinesis data firehose buffer interval',
      min_value=60,
      max_value=300,
      default=60
    )

    FIREHOSE_LAMBDA_BUFFER_SIZE = cdk.CfnParameter(self, 'FirehoseLambdaBufferSize',
      type='Number',
      description='kinesis data firehose buffer size for AWS Lambda to transform records',
      min_value=1,
      max_value=3,
      default=3
    )

    FIREHOSE_LAMBDA_BUFFER_INTERVAL = cdk.CfnParameter(self, 'FirehoseLambdaBufferInterval',
      type='Number',
      description='kinesis data firehose buffer interval for AWS Lambda to transform records',
      min_value=60,
      max_value=900,
      default=300
    )

    FIREHOSE_LAMBDA_NUMBER_OF_RETRIES = cdk.CfnParameter(self, 'FirehoseLambdaNumberOfRetries',
      type='Number',
      description='Number of retries for AWS Lambda to transform records in kinesis data firehose',
      min_value=1,
      max_value=5,
      default=3
    )

    FIREHOSE_TO_S3_PREFIX = cdk.CfnParameter(self, 'FirehosePrefix',
      type='String',
      description='kinesis data firehose S3 prefix',
      default='json-data/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/'
    )

    FIREHOSE_TO_S3_ERROR_OUTPUT_PREFIX = cdk.CfnParameter(self, 'FirehoseErrorOutputPrefix',
      type='String',
      description='kinesis data firehose S3 error output prefix',
      default='error/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/!{firehose:error-output-type}'
    )

    firehose_role_policy_doc = aws_iam.PolicyDocument()

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [s3_bucket.bucket_arn, "{}/*".format(s3_bucket.bucket_arn)],
      "actions": ["s3:AbortMultipartUpload",
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:PutObject"]
    }))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=["ec2:DescribeVpcs",
        "ec2:DescribeVpcAttribute",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeNetworkInterfaces",
        "ec2:CreateNetworkInterface",
        "ec2:CreateNetworkInterfacePermission",
        "ec2:DeleteNetworkInterface"]
    ))

    firehose_log_group_name = "/aws/kinesisfirehose/{}".format(FIREHOSE_STREAM_NAME.value_as_string)
    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
      resources=[self.format_arn(service="logs", resource="log-group",
        resource_name="{}:log-stream:*".format(firehose_log_group_name),
        arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      actions=["logs:PutLogEvents"]
    ))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [f"{data_transform_lambda_fn.function_arn}:*"],
      "actions": [
        "lambda:InvokeFunction",
        "lambda:GetFunctionConfiguration"
      ]
    }))

    firehose_role = aws_iam.Role(self, "KinesisFirehoseServiceRole",
      role_name="KinesisFirehoseServiceRole-{stream_name}-{region}".format(
        stream_name=FIREHOSE_STREAM_NAME.value_as_string, region=cdk.Aws.REGION),
      assumed_by=aws_iam.ServicePrincipal("firehose.amazonaws.com"),
      #XXX: use inline_policies to work around https://github.com/aws/aws-cdk/issues/5221
      inline_policies={
        "firehose_role_policy": firehose_role_policy_doc
      }
    )

    lambda_proc = cfn.ProcessorProperty(
      type="Lambda",
      parameters=[
        cfn.ProcessorParameterProperty(
          parameter_name="LambdaArn",
          # parameter_value='{}:{}'.format(schema_validator_lambda_fn.function_arn, schema_validator_lambda_fn.current_version.version)
          parameter_value='{}:{}'.format(data_transform_lambda_fn.function_arn, data_transform_lambda_fn.latest_version.version)
        ),
        cfn.ProcessorParameterProperty(
          parameter_name="NumberOfRetries",
          parameter_value=FIREHOSE_LAMBDA_NUMBER_OF_RETRIES.value_as_string
        ),
        cfn.ProcessorParameterProperty(
          parameter_name="RoleArn",
          parameter_value=firehose_role.role_arn
        ),
        cfn.ProcessorParameterProperty(
          parameter_name="BufferSizeInMBs",
          parameter_value=FIREHOSE_LAMBDA_BUFFER_SIZE.value_as_string
        ),
        cfn.ProcessorParameterProperty(
          parameter_name="BufferIntervalInSeconds",
          parameter_value=FIREHOSE_LAMBDA_BUFFER_INTERVAL.value_as_string
        )
      ]
    )

    firehose_processing_config = cfn.ProcessingConfigurationProperty(
      enabled=True,
      processors=[
        lambda_proc
      ]
    )

    ext_s3_dest_config = cfn.ExtendedS3DestinationConfigurationProperty(
      bucket_arn=s3_bucket.bucket_arn,
      role_arn=firehose_role.role_arn,
      buffering_hints={
        "intervalInSeconds": FIREHOSE_BUFFER_INTERVAL.value_as_number,
        "sizeInMBs": FIREHOSE_BUFFER_SIZE.value_as_number
      },
      cloud_watch_logging_options={
        "enabled": True,
        "logGroupName": firehose_log_group_name,
        "logStreamName": "DestinationDelivery"
      },
      compression_format="UNCOMPRESSED", # [GZIP | HADOOP_SNAPPY | Snappy | UNCOMPRESSED | ZIP]
      data_format_conversion_configuration={
        "enabled": False
      },
      dynamic_partitioning_configuration={
        "enabled": False
      },
      error_output_prefix=FIREHOSE_TO_S3_ERROR_OUTPUT_PREFIX.value_as_string,
      prefix=FIREHOSE_TO_S3_PREFIX.value_as_string,
      processing_configuration=firehose_processing_config
    )

    firehose_to_s3_delivery_stream = aws_kinesisfirehose.CfnDeliveryStream(self, "FirehoseToS3",
      delivery_stream_name=FIREHOSE_STREAM_NAME.value_as_string,
      delivery_stream_type="DirectPut",
      extended_s3_destination_configuration=ext_s3_dest_config,
      tags=[{"key": "Name", "value": FIREHOSE_STREAM_NAME.value_as_string}]
    )


    cdk.CfnOutput(self, 'S3DestBucket'.format(self.stack_name),
      value=s3_bucket.bucket_name,
      export_name=f'{self.stack_name}-S3DestBucket')
    cdk.CfnOutput(self, 'KinesisDataFirehoseStreamName',
      value=firehose_to_s3_delivery_stream.delivery_stream_name,
      export_name=f'{self.stack_name}-FirehoseStreamName')
