#!/usr/bin/env python3
import os

from aws_cdk import (
  core as cdk,
  aws_ec2,
  aws_iam,
  aws_s3 as s3,
  aws_kinesisfirehose
)

class FirehoseToS3Stack(cdk.Stack):

  def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # vpc_name = self.node.try_get_context("vpc_name")
    # vpc = aws_ec2.Vpc.from_lookup(self, "ExistingVPC",
    #   is_default=True,
    #   vpc_name=vpc_name)
    vpc = aws_ec2.Vpc(self, "FirehoseToS3VPC",
      max_azs=2,
      gateway_endpoints={
        "S3": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.S3
        )
      }
    )

    S3_BUCKET_SUFFIX = ''.join(random.sample((string.ascii_lowercase + string.digits), k=7))
    s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=core.RemovalPolicy.DESTROY, #XXX: Default: core.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name="firehose-to-s3-{region}-{suffix}".format(
        region=core.Aws.REGION, suffix=S3_BUCKET_SUFFIX))

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

    firehose_log_group_name = "/aws/kinesisfirehose/{}".format(ES_INDEX_NAME)
    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
      resources=[self.format_arn(service="logs", resource="log-group",
        resource_name="{}:log-stream:*".format(firehose_log_group_name), sep=":")],
      actions=["logs:PutLogEvents"]
    ))

    firehose_role = aws_iam.Role(self, "KinesisFirehoseServiceRole",
      role_name="KinesisFirehoseServiceRole-{es_index}-{region}".format(es_index=ES_INDEX_NAME, region=core.Aws.REGION),
      assumed_by=aws_iam.ServicePrincipal("firehose.amazonaws.com"),
      #XXX: use inline_policies to work around https://github.com/aws/aws-cdk/issues/5221
      inline_policies={
        "firehose_role_policy": firehose_role_policy_doc
      }
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

    ext_s3_dest_config = aws_kinesisfirehose.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
      bucket_arn=s3_bucket.bucket_arn,
      role_arn= ,
      buffering_hints= ,
      dynamic_partitioning_configuration= ,
      error_output_prefix=FIREHOSE_TO_S3_ERROR_OUTPUT_PREFIX,
      prefix=FIREHOSE_TO_S3_PREFIX,
      processing_configuration=
    )

    FIREHOSE_STREAM_NAME = cdk.CfnParameter(self, 'FirehoseStreamName',
      type='String',
      description='kinesis data firehose stream name'
    )

    firehose_to_s3_delivery_stream = aws_kinesisfirehose.CfnDeliveryStream(self, "FirehoseToS3",
      delivery_stream_name=FIREHOSE_STREAM_NAME,
      delivery_stream_type="DirectPut",
      extended_s3_destination_configuration=ext_s3_dest_config,
      tags=[{"key": "Name", "value": FIREHOSE_STREAM_NAME}]
    )

    cdk.CfnOutput(self, 'StackName', value=self.stack_name, export_name='StackName')
    cdk.CfnOutput(self, f'{FIREHOSE_STREAM_NAME}_S3DestBucket', value=s3_bucket.bucket_name, export_name='S3DestBucket')


app = cdk.App()
FirehoseToS3Stack(app, "FirehoseToS3Stack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
