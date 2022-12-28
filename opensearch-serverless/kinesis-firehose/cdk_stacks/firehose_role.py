#!/usr/bin/env python3

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


class KinesisFirehoseRoleStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    firehose_config = self.node.try_get_context('firehose')
    OPENSEARCH_INDEX_NAME = firehose_config['opensearch_index_name']

    S3_BUCKET_SUFFIX = ''.join(random.sample((string.ascii_lowercase + string.digits), k=7))
    s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: core.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name="firehose-to-ops-{region}-{suffix}".format(
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

    # firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
    #   effect=aws_iam.Effect.ALLOW,
    #   resources=["*"],
    #   actions=["es:DescribeElasticsearchDomain",
    #     "es:DescribeElasticsearchDomains",
    #     "es:DescribeElasticsearchDomainConfig",
    #     "es:ESHttpPost",
    #     "es:ESHttpPut"]
    # ))

    # firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
    #   effect=aws_iam.Effect.ALLOW,
    #   #XXX: https://aws.amazon.com/premiumsupport/knowledge-center/kinesis-data-firehose-delivery-failure/
    #   resources=[
    #     ops_domain_arn,
    #     f"{ops_domain_arn}/_all/_settings",
    #     f"{ops_domain_arn}/_cluster/stats",
    #     f"{ops_domain_arn}/{OPENSEARCH_INDEX_NAME}*/_mapping/%FIREHOSE_POLICY_TEMPLATE_PLACEHOLDER%",
    #     f"{ops_domain_arn}/_nodes",
    #     f"{ops_domain_arn}/_nodes/stats",
    #     f"{ops_domain_arn}/_nodes/*/stats",
    #     f"{ops_domain_arn}/_stats",
    #     f"{ops_domain_arn}/{OPENSEARCH_INDEX_NAME}*/_stats"
    #   ],
    #   actions=["es:ESHttpGet"]
    # ))

    firehose_log_group_name = f"/aws/kinesisfirehose/{OPENSEARCH_INDEX_NAME}"
    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
      resources=[self.format_arn(service="logs", resource="log-group",
        resource_name="{}:log-stream:*".format(firehose_log_group_name), arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      actions=["logs:PutLogEvents"]
    ))

    firehose_role = aws_iam.Role(self, "KinesisFirehoseServiceRole",
      role_name=f"KinesisFirehoseServiceRole-{self.stack_name}",
      assumed_by=aws_iam.ServicePrincipal("firehose.amazonaws.com"),
      #XXX: use inline_policies to work around https://github.com/aws/aws-cdk/issues/5221
      inline_policies={
        "firehose_role_policy": firehose_role_policy_doc
      }
    )

    self.firehose_role = firehose_role
    self.firehose_role_name = firehose_role.role_name
