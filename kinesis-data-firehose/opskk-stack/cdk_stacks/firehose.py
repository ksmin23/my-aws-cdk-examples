#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_s3 as s3,
  aws_kinesisfirehose
)
from constructs import Construct

random.seed(47)


class KinesisFirehoseStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, opensearch_domain, opensearch_index_name, sg_opensearch_client, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    S3_BUCKET_SUFFIX = ''.join(random.sample((string.ascii_lowercase + string.digits), k=7))
    s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: core.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name="opskk-stack-{region}-{suffix}".format(
        region=cdk.Aws.REGION, suffix=S3_BUCKET_SUFFIX))

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

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=[opensearch_domain.domain_arn, "{}/*".format(opensearch_domain.domain_arn)],
      actions=["es:DescribeElasticsearchDomain",
        "es:DescribeElasticsearchDomains",
        "es:DescribeElasticsearchDomainConfig",
        "es:ESHttpPost",
        "es:ESHttpPut"]
    ))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      #XXX: https://aws.amazon.com/premiumsupport/knowledge-center/kinesis-data-firehose-delivery-failure/
      resources=[
        opensearch_domain.domain_arn,
        f"{opensearch_domain.domain_arn}/_all/_settings",
        f"{opensearch_domain.domain_arn}/_cluster/stats",
        f"{opensearch_domain.domain_arn}/{opensearch_index_name}*/_mapping/%FIREHOSE_POLICY_TEMPLATE_PLACEHOLDER%",
        f"{opensearch_domain.domain_arn}/_nodes",
        f"{opensearch_domain.domain_arn}/_nodes/stats",
        f"{opensearch_domain.domain_arn}/_nodes/*/stats",
        f"{opensearch_domain.domain_arn}/_stats",
        f"{opensearch_domain.domain_arn}/{opensearch_index_name}*/_stats"
      ],
      actions=["es:ESHttpGet"]
    ))

    firehose_log_group_name = f"/aws/kinesisfirehose/{opensearch_index_name}"
    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
      resources=[self.format_arn(service="logs", resource="log-group",
        resource_name="{}:log-stream:*".format(firehose_log_group_name), arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      actions=["logs:PutLogEvents"]
    ))

    firehose_role = aws_iam.Role(self, "KinesisFirehoseServiceRole",
      role_name=f"KinesisFirehoseServiceRole-{opensearch_index_name}-{cdk.Aws.REGION}",
      assumed_by=aws_iam.ServicePrincipal("firehose.amazonaws.com"),
      #XXX: use inline_policies to work around https://github.com/aws/aws-cdk/issues/5221
      inline_policies={
        "firehose_role_policy": firehose_role_policy_doc
      }
    )

    opensearch_dest_vpc_config = aws_kinesisfirehose.CfnDeliveryStream.VpcConfigurationProperty(
      role_arn=firehose_role.role_arn,
      security_group_ids=[sg_opensearch_client.security_group_id],
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
    )

    opensearch_dest_config = aws_kinesisfirehose.CfnDeliveryStream.ElasticsearchDestinationConfigurationProperty(
      index_name=opensearch_index_name,
      role_arn=firehose_role.role_arn,
      s3_configuration={
        "bucketArn": s3_bucket.bucket_arn,
        "bufferingHints": {
          "intervalInSeconds": 60,
          "sizeInMBs": 1
        },
        "cloudWatchLoggingOptions": {
          "enabled": True,
          "logGroupName": firehose_log_group_name,
          "logStreamName": "S3Backup"
        },
        "compressionFormat": "UNCOMPRESSED", # [GZIP | HADOOP_SNAPPY | Snappy | UNCOMPRESSED | ZIP]
        # Kinesis Data Firehose automatically appends the “YYYY/MM/dd/HH/” UTC prefix to delivered S3 files. You can also specify
        # an extra prefix in front of the time format and add "/" to the end to have it appear as a folder in the S3 console.
        "prefix": f"{opensearch_index_name}/",
        "roleArn": firehose_role.role_arn
      },
      buffering_hints={
        "intervalInSeconds": 60,
        "sizeInMBs": 1
      },
      cloud_watch_logging_options={
        "enabled": True,
        "logGroupName": firehose_log_group_name,
        "logStreamName": "ElasticsearchDelivery"
      },
      domain_arn=opensearch_domain.domain_arn,
      #XXX: Index rotation appends a timestamp to the IndexName to facilitate the expiration of old data.
      # For more information, see https://docs.aws.amazon.com/firehose/latest/dev/create-destination.html#create-destination-elasticsearch
      # For more information about allowed values,
      # see https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-kinesisfirehose-deliverystream-amazonopensearchservicedestinationconfiguration.html#cfn-kinesisfirehose-deliverystream-amazonopensearchservicedestinationconfiguration-indexrotationperiod
      index_rotation_period="NoRotation", # [NoRotation | OneDay | OneHour | OneMonth | OneWeek]
      retry_options={
        "durationInSeconds": 60
      },
      s3_backup_mode="FailedDocumentsOnly", # [AllDocuments | FailedDocumentsOnly]
      vpc_configuration=opensearch_dest_vpc_config
    )

    firehose_to_ops_delivery_stream = aws_kinesisfirehose.CfnDeliveryStream(self, "KinesisFirehoseToES",
      delivery_stream_name=opensearch_index_name,
      delivery_stream_type="DirectPut",
      elasticsearch_destination_configuration=opensearch_dest_config,
      tags=[{"key": "Name", "value": opensearch_index_name}]
    )


    cdk.CfnOutput(self, 'S3DestBucket',
      value=s3_bucket.bucket_name,
      export_name=f'{self.stack_name}-S3DestBucket')
    cdk.CfnOutput(self, 'FirehoseRoleArn',
      value=firehose_role.role_arn,
      export_name=f'{self.stack_name}-FirehoseRoleArn')
