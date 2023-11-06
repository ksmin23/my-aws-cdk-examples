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


class KinesisFirehoseStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, msk_cluster_name, msk_cluster_arn, s3_bucket, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    firehose_role_policy_doc = aws_iam.PolicyDocument()
    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [s3_bucket.bucket_arn, f"{s3_bucket.bucket_arn}/*"],
      "actions": ["s3:AbortMultipartUpload",
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:PutObject"]
    }))

    firehose_delivery_stream_name = f"{msk_cluster_name}-to-s3"
    firehose_log_group_name = f"/aws/kinesisfirehose/{firehose_delivery_stream_name}"
    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
      resources=[self.format_arn(service="logs", resource="log-group",
        resource_name=f"{firehose_log_group_name}:log-stream:*",
        arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      actions=["logs:PutLogEvents"]
    ))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [ f"arn:aws:kafka:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:cluster/{msk_cluster_name}/*" ],
      "actions": [
        "kafka:GetBootstrapBrokers",
        "kafka:DescribeCluster",
        "kafka:DescribeClusterV2",
        "kafka-cluster:Connect"
      ]
    }))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [ f"arn:aws:kafka:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:topic/{msk_cluster_name}/*" ],
      "actions": [
        "kafka-cluster:DescribeTopic",
        "kafka-cluster:DescribeTopicDynamicConfiguration",
        "kafka-cluster:ReadData"
      ]
    }))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [ f"arn:aws:kafka:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:group/{msk_cluster_name}/*" ],
      "actions": [
        "kafka-cluster:DescribeGroup"
      ]
    }))

    firehose_role = aws_iam.Role(self, "KinesisFirehoseServiceRole",
      role_name=f"KinesisFirehoseServiceRole-{msk_cluster_name}-{cdk.Aws.REGION}",
      assumed_by=aws_iam.ServicePrincipal("firehose.amazonaws.com"),
      #XXX: use inline_policies to work around https://github.com/aws/aws-cdk/issues/5221
      inline_policies={
        "firehose_role_policy": firehose_role_policy_doc
      }
    )

    firehose_config = self.node.try_get_context("firehose")
    kafka_topic_name = firehose_config['topic_name']
    firehose_buffering_hints = firehose_config['buffering_hints']

    extended_s3_dest_config = aws_kinesisfirehose.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
      bucket_arn=s3_bucket.bucket_arn,
      role_arn=firehose_role.role_arn,
      buffering_hints=firehose_buffering_hints,
      cloud_watch_logging_options={
        "enabled": True,
        "logGroupName": firehose_log_group_name,
        "logStreamName": "DestinationDelivery"
      },
      compression_format="UNCOMPRESSED", # [GZIP | HADOOP_SNAPPY | Snappy | UNCOMPRESSED | ZIP]
      data_format_conversion_configuration={
        "enabled": False
      },
      processing_configuration={
        "enabled": False
      },
      error_output_prefix="error-json/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/!{firehose:error-output-type}",
      prefix="json-data/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
    )

    firehose_delivery_stream = aws_kinesisfirehose.CfnDeliveryStream(self, "KDFfromMSKtoS3",
      delivery_stream_name=firehose_delivery_stream_name,
      delivery_stream_type="MSKAsSource",
      msk_source_configuration=aws_kinesisfirehose.CfnDeliveryStream.MSKSourceConfigurationProperty(
        authentication_configuration = {
          'connectivity': 'PRIVATE', # [PRIVATE | PUBLIC]
          'roleArn': firehose_role.role_arn,
        },
        msk_cluster_arn=msk_cluster_arn,
        topic_name=kafka_topic_name
      ),
      extended_s3_destination_configuration=extended_s3_dest_config
    )

    cdk.CfnOutput(self, 'S3DestBucketName', value=s3_bucket.bucket_name,
      export_name=f'{self.stack_name}-S3DestBucketName')
    cdk.CfnOutput(self, 'S3DestBucketArn', value=firehose_delivery_stream.extended_s3_destination_configuration.bucket_arn,
      export_name=f'{self.stack_name}-S3DestBucketArn')
    cdk.CfnOutput(self, 'FirehoseRoleArn', value=firehose_role.role_arn,
      export_name=f'{self.stack_name}-FirehoseRoleArn')
    cdk.CfnOutput(self, 'MSKClusterArn', value=firehose_delivery_stream.msk_source_configuration.msk_cluster_arn,
      export_name=f'{self.stack_name}-MSKClusterArn')
    cdk.CfnOutput(self, 'MSKAsSourceTopicName', value=firehose_delivery_stream.msk_source_configuration.topic_name,
      export_name=f'{self.stack_name}-MSKAsSourceTopicName')

