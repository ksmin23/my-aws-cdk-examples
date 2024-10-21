#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam,
  aws_s3 as s3,
  aws_kinesisfirehose
)
from constructs import Construct

from aws_cdk.aws_kinesisfirehose import CfnDeliveryStream as cfn


class FirehoseToIcebergStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, data_transform_lambda_fn, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    s3_bucket_name = self.node.try_get_context("s3_bucket_name")
    s3_bucket = s3.Bucket.from_bucket_name(self, "s3bucket", s3_bucket_name)

    firehose_stream_name = self.node.try_get_context("stream_name")

    firehose_buffering_hints = self.node.try_get_context("buffering_hints")
    firehose_buffer_size = firehose_buffering_hints["size_in_mbs"]
    firehose_buffer_interval = firehose_buffering_hints["interval_in_seconds"]

    transform_records_with_aws_lambda = self.node.try_get_context("transform_records_with_aws_lambda")
    firehose_lambda_buffer_size = transform_records_with_aws_lambda["buffer_size"]
    firehose_lambda_buffer_interval = transform_records_with_aws_lambda["buffer_interval"]
    firehose_lambda_number_of_retries = transform_records_with_aws_lambda["number_of_retries"]

    s3_output_prefix = self.node.try_get_context("output_prefix")
    s3_error_output_prefix = self.node.try_get_context("error_output_prefix")


    firehose_role_policy_doc = aws_iam.PolicyDocument()

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [s3_bucket.bucket_arn, "{}/*".format(s3_bucket.bucket_arn)],
      "actions": [
        "s3:AbortMultipartUpload",
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:PutObject"
      ]
    }))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [
        f"arn:aws:glue:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:catalog",
        f"arn:aws:glue:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:database/*",
        f"arn:aws:glue:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:table/*"
      ],
      "actions": [
        "glue:GetTable",
        "glue:GetTables",
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:CreateTable",
        "glue:UpdateTable",
        "glue:DeleteTable",
        "glue:BatchCreatePartition",
        "glue:BatchDeletePartition"
      ]
    }))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=[
        "ec2:DescribeVpcs",
        "ec2:DescribeVpcAttribute",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeNetworkInterfaces",
        "ec2:CreateNetworkInterface",
        "ec2:CreateNetworkInterfacePermission",
        "ec2:DeleteNetworkInterface"
      ]
    ))

    #XXX: https://docs.aws.amazon.com/ko_kr/cdk/latest/guide/tokens.html
    # String-encoded tokens:
    #  Avoid manipulating the string in other ways. For example,
    #  taking a substring of a string is likely to break the string token.
    firehose_log_group_name = f"/aws/kinesisfirehose/{firehose_stream_name}"
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
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
      "resources": [self.format_arn(partition="aws", service="lambda",
        region=cdk.Aws.REGION, account=cdk.Aws.ACCOUNT_ID, resource="function",
        resource_name="{}:*".format(data_transform_lambda_fn.function_name),
        arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      "actions": ["lambda:InvokeFunction",
        "lambda:GetFunctionConfiguration"]
    }))

    firehose_role = aws_iam.Role(self, "KinesisFirehoseServiceRole",
      role_name="KinesisFirehoseServiceRole-{stream_name}-{region}".format(
        stream_name=firehose_stream_name, region=cdk.Aws.REGION),
      assumed_by=aws_iam.ServicePrincipal("firehose.amazonaws.com"),
      path='/service-role/',
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
          parameter_value='{}:{}'.format(data_transform_lambda_fn.function_arn, data_transform_lambda_fn.latest_version.version)
        ),
        cfn.ProcessorParameterProperty(
          parameter_name="NumberOfRetries",
          parameter_value=str(firehose_lambda_number_of_retries)
        ),
        cfn.ProcessorParameterProperty(
          parameter_name="RoleArn",
          parameter_value=firehose_role.role_arn
        ),
        cfn.ProcessorParameterProperty(
          parameter_name="BufferSizeInMBs",
          parameter_value=str(firehose_lambda_buffer_size)
        ),
        cfn.ProcessorParameterProperty(
          parameter_name="BufferIntervalInSeconds",
          parameter_value=str(firehose_lambda_buffer_interval)
        )
      ]
    )

    firehose_processing_config = cfn.ProcessingConfigurationProperty(
      enabled=True,
      processors=[
        lambda_proc
      ]
    )

    dest_iceberg_table_config = self.node.try_get_context("destination_iceberg_table_configuration")

    iceberg_dest_config = cfn.IcebergDestinationConfigurationProperty(
      catalog_configuration=cfn.CatalogConfigurationProperty(
        catalog_arn=f"arn:aws:glue:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:catalog"
      ),
      role_arn=firehose_role.role_arn,
      s3_configuration=cfn.S3DestinationConfigurationProperty(
        bucket_arn=s3_bucket.bucket_arn,
        role_arn=firehose_role.role_arn,
        buffering_hints={
          "intervalInSeconds": firehose_buffer_interval,
          "sizeInMBs": firehose_buffer_size
        },
        cloud_watch_logging_options={
          "enabled": True,
          "logGroupName": firehose_log_group_name,
          "logStreamName": "DestinationDelivery"
        },
        # compression_format="UNCOMPRESSED", # [GZIP | HADOOP_SNAPPY | Snappy | UNCOMPRESSED | ZIP]
        error_output_prefix=s3_error_output_prefix,
        prefix=s3_output_prefix,
      ),
      buffering_hints={
        "intervalInSeconds": firehose_buffer_interval,
        "sizeInMBs": firehose_buffer_size
      },
      cloud_watch_logging_options={
        "enabled": True,
        "logGroupName": firehose_log_group_name,
        "logStreamName": "DestinationDelivery"
      },
      destination_table_configuration_list=[
        cfn.DestinationTableConfigurationProperty(
          destination_database_name=dest_iceberg_table_config["database_name"],
          destination_table_name=dest_iceberg_table_config["table_name"],
          s3_error_output_prefix=s3_error_output_prefix,
          unique_keys=dest_iceberg_table_config["unique_keys"]
        )
      ],
      processing_configuration=firehose_processing_config,
      s3_backup_mode='FailedDataOnly'
    )

    firehose_to_iceberg_delivery_stream = aws_kinesisfirehose.CfnDeliveryStream(self, "FirehoseToIceberg",
      delivery_stream_name=firehose_stream_name,
      delivery_stream_type="DirectPut",
      iceberg_destination_configuration=iceberg_dest_config,
      tags=[{"key": "Name", "value": firehose_stream_name}]
    )

    cdk.CfnOutput(self, 'S3DestBucket',
      value=s3_bucket.bucket_name,
      export_name=f'{self.stack_name}-S3DestBucket')