#!/usr/bin/env python3
import os
import random
import string

import aws_cdk as cdk

from aws_cdk import (
  # Duration,
  Stack,
  aws_iam,
  aws_s3 as s3,
  aws_kinesis,
  aws_kinesisfirehose,
  aws_logs
)
from constructs import Construct

class KDS2KDFStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    S3_BUCKET_SUFFIX = ''.join(random.sample((string.ascii_lowercase + string.digits), k=7))
    s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: cdk.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name="aws-kinesis-streams-to-firehose-to-s3-{region}-{suffix}".format(
        region=cdk.Aws.REGION, suffix=S3_BUCKET_SUFFIX))

    KINESIS_STREAM_NAME = cdk.CfnParameter(self, 'KinesisStreamName',
      type='String',
      description='kinesis data stream name',
      default='PUT-Firehose-{}'.format(''.join(random.sample((string.ascii_letters), k=5)))
    )

    FIREHOSE_STREAM_NAME = cdk.CfnParameter(self, 'FirehoseStreamName',
      type='String',
      description='kinesis data firehose name',
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

    input_kinesis_stream = aws_kinesis.Stream(self, "InputKinesisStreams", stream_name=KINESIS_STREAM_NAME.value_as_string)
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
      actions=["glue:GetTable",
        "glue:GetTableVersion",
        "glue:GetTableVersions"]
    ))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=[input_kinesis_stream.stream_arn],
      actions=["kinesis:DescribeStream",
        "kinesis:GetShardIterator",
        "kinesis:GetRecords"]
    ))

    firehose_log_group_name = f"/aws/kinesisfirehose/{FIREHOSE_STREAM_NAME.value_as_string}"
    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
      resources=[self.format_arn(service="logs", resource="log-group",
        resource_name="{}:log-stream:*".format(firehose_log_group_name),
        arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      actions=["logs:PutLogEvents"]
    ))

    firehose_role = aws_iam.Role(self, "KinesisFirehoseDeliveryRole",
      role_name="KinesisFirehoseServiceRole-{stream_name}-{region}".format(
        stream_name=FIREHOSE_STREAM_NAME.value_as_string, region=cdk.Aws.REGION),
      assumed_by=aws_iam.ServicePrincipal("firehose.amazonaws.com"),
      #XXX: use inline_policies to work around https://github.com/aws/aws-cdk/issues/5221
      inline_policies={
        "firehose_role_policy": firehose_role_policy_doc
      }
    )

    firehose_to_s3_delivery_stream = aws_kinesisfirehose.CfnDeliveryStream(self, "KinesisFirehoseToS3",
      delivery_stream_name=FIREHOSE_STREAM_NAME.value_as_string,
      delivery_stream_type="KinesisStreamAsSource",
      kinesis_stream_source_configuration={
        "kinesisStreamArn": input_kinesis_stream.stream_arn,
        "roleArn": firehose_role.role_arn
      },
      extended_s3_destination_configuration={
        "bucketArn": s3_bucket.bucket_arn,
        "bufferingHints": {
          "intervalInSeconds": 60,
          "sizeInMBs": 1
        },
        "cloudWatchLoggingOptions": {
          "enabled": True,
          "logGroupName": firehose_log_group_name,
          "logStreamName": "S3Delivery"
        },
        "compressionFormat": "UNCOMPRESSED", # [GZIP | HADOOP_SNAPPY | Snappy | UNCOMPRESSED | ZIP]
        "prefix": FIREHOSE_TO_S3_PREFIX.value_as_string,
        "errorOutputPrefix": FIREHOSE_TO_S3_ERROR_OUTPUT_PREFIX.value_as_string,
        "roleArn": firehose_role.role_arn
      }
    )

    cdk.CfnOutput(self, '{}_S3DestBucket'.format(self.stack_name), value=s3_bucket.bucket_name, export_name='S3DestBucket')
    cdk.CfnOutput(self, '{}_KinesisDataStreamName'.format(self.stack_name), value=input_kinesis_stream.stream_name, export_name='KinesisDataStreamName')
    cdk.CfnOutput(self, '{}_KinesisDataFirehoseName'.format(self.stack_name), value=firehose_to_s3_delivery_stream.delivery_stream_name, export_name='KinesisDataFirehoseName')


app = cdk.App()
KDS2KDFStack(app, "KinesisDataStreamsToFirehoseStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
