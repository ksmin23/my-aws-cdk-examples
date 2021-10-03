#!/usr/bin/env python3
import os
import json
import random
import string

from aws_cdk import (
  core as cdk,
  aws_ec2,
  aws_iam,
  aws_lambda,
  aws_logs,
  aws_s3 as s3,
  aws_kinesisfirehose
)

from aws_cdk.aws_kinesisfirehose import CfnDeliveryStream as cfn

random.seed(31)

class FirehoseToS3LambdaStack(cdk.Stack):

  def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    vpc_name = self.node.try_get_context("vpc_name")
    vpc = aws_ec2.Vpc.from_lookup(self, "ExistingVPC",
      is_default=True,
      vpc_name=vpc_name)
    # vpc = aws_ec2.Vpc(self, "FirehoseToS3VPC",
    #   max_azs=2,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )

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

    FIREHOSE_BUFFER_SIZE=cdk.CfnParameter(self, 'FirehoseBufferSize',
      type='Number',
      description='kinesis data firehose buffer size',
      min_value=1,
      max_value=128,
      default=128
    )

    FIREHOSE_BUFFER_INTERVAL=cdk.CfnParameter(self, 'FirehoseBufferInterval',
      type='Number',
      description='kinesis data firehose buffer interval',
      min_value=60,
      max_value=300,
      default=60
    )

    FIREHOSE_TO_S3_PREFIX = cdk.CfnParameter(self, 'FirehosePrefix',
      type='String',
      description='kinesis data firehose S3 prefix'
    )

    FIREHOSE_TO_S3_ERROR_OUTPUT_PREFIX = cdk.CfnParameter(self, 'FirehoseErrorOutputPrefix',
      type='String',
      description='kinesis data firehose S3 error output prefix',
      default='error/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/!{firehose:error-output-type}'
    )

    metadata_extract_lambda_fn = aws_lambda.Function(self, "MetadataExtractor",
      runtime=aws_lambda.Runtime.PYTHON_3_7,
      function_name="MetadataExtractor",
      handler="metadata_extractor.lambda_handler",
      description="Extract partition keys from records",
      code=aws_lambda.Code.asset(os.path.join(os.path.dirname(__file__), 'src/main/python')),
      timeout=cdk.Duration.minutes(5)
    )

    metadata_extract_lambda_fn.add_to_role_policy(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      resources=[self.format_arn(partition="aws", service="logs", region=cdk.Aws.REGION, 
        account=cdk.Aws.ACCOUNT_ID,resource="*")],
      actions=["logs:CreateLogGroup"]
    ))

    metadata_extract_lambda_fn.add_to_role_policy(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      resources=[self.format_arn(partition="aws", service="logs", region=cdk.Aws.REGION, 
        account=cdk.Aws.ACCOUNT_ID, resource="log-group",
        resource_name="/aws/lambda/MetadataExtractor:*", sep=":")
      ],
      actions=[
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
    ))
  
    # log_group = aws_logs.LogGroup(self, "MetadataExtractorLogGroup",
    #   log_group_name="/aws/lambda/{}".format(metadata_extract_lambda_fn.function_name),
    #   retention=aws_logs.RetentionDays.THREE_DAYS,
    #   removal_policy=cdk.RemovalPolicy.DESTROY
    # )
    # log_group.grant_write(metadata_extract_lambda_fn)
  
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
        resource_name="{}:log-stream:*".format(firehose_log_group_name), sep=":")],
      actions=["logs:PutLogEvents"]
    ))

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
          parameter_value=metadata_extract_lambda_fn.function_arn
        ),
        cfn.ProcessorParameterProperty(
          parameter_name="NumberOfRetries",
          parameter_value="3"
        ),
        cfn.ProcessorParameterProperty(
          parameter_name="RoleArn",
          parameter_value=firehose_role.role_arn
        ),
        cfn.ProcessorParameterProperty(
          parameter_name="BufferSizeInMBs",
          parameter_value="3" # 1~3MiBs
        ),
        cfn.ProcessorParameterProperty(
          parameter_name="BufferIntervalInSeconds",
          parameter_value="300" # 60~900 sec
        )
      ]
    )

    record_deaggregation_proc = cfn.ProcessorProperty(
      type="RecordDeAggregation",
      parameters=[
        cfn.ProcessorParameterProperty(
          parameter_name="SubRecordType",
          parameter_value="JSON"
        )
      ]
    )

    #XXX: Adding a new line delimiter when delivering data to S3
    # This is also particularly useful when dynamic partitioning is applied to aggregated data
    # because multirecord deaggregation (which must be applied to aggregated data 
    # before it can be dynamically partitioned) removes new lines from records as part of the parsing process.
    # https://docs.aws.amazon.com/firehose/latest/dev/dynamic-partitioning.html#dynamic-partitioning-new-line-delimiter
    append_delim_to_record_proc = cfn.ProcessorProperty(
      type="AppendDelimiterToRecord",
      parameters=[]
    )

    firehose_processing_config = cfn.ProcessingConfigurationProperty(
      enabled=True,
      processors=[
        record_deaggregation_proc,
        append_delim_to_record_proc,
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
        "enabled": True,
        "retryOptions": {
          "durationInSeconds": 300
        }
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

    #cdk.CfnOutput(self, 'StackName', value=self.stack_name, export_name='StackName')
    #cdk.CfnOutput(self, '{}_S3DestBucket'.format(self.stack_name), value=s3_bucket.bucket_name, export_name='S3DestBucket')


app = cdk.App()
FirehoseToS3LambdaStack(app, "FirehoseToS3LambdaStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
