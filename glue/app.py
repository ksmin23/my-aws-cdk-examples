#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_glue,
  aws_iam,
  aws_s3 as s3,
)
from constructs import Construct


class GlueJobStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    vpc_name = self.node.try_get_context('vpc_name')
    vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
      is_default=True,
      vpc_name=vpc_name
    )

    # vpc = aws_ec2.Vpc(self, 'DMSAuroraMysqlToS3VPC',
    #   max_azs=3,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )

    glue_job_role_policy_doc = aws_iam.PolicyDocument()
    glue_job_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AWSGlueJobDynamoDBAccess",
      "effect": aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [self.format_arn(service="dynamodb", resource="table", resource_name="*")],
      "actions": [
        "dynamodb:BatchGetItem",
        "dynamodb:DescribeStream",
        "dynamodb:DescribeTable",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchWriteItem",
        "dynamodb:CreateTable",
        "dynamodb:DeleteTable",
        "dynamodb:UpdateTable",
        "dynamodb:UpdateItem",
        "dynamodb:PutItem"
      ]
    }))

    glue_job_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AWSGlueJobS3Access",
      "effect": aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": ["*"],
      "actions": [
        "s3:GetBucketLocation",
        "s3:ListBucket",
        "s3:GetBucketAcl",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ]
    }))

    glue_job_role = aws_iam.Role(self, 'GlueJobRole',
      role_name='GlueJobRole',
      assumed_by=aws_iam.ServicePrincipal('glue.amazonaws.com'),
      inline_policies={
        'aws_glue_job_role_policy': glue_job_role_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSGlueServiceRole'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMReadOnlyAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonEC2ContainerRegistryReadOnly'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AWSGlueConsoleFullAccess')
      ]
    )

    glue_assets_s3_bucket_name = self.node.try_get_context('glue_assets_s3_bucket_name')
    glue_job_script_file_name = self.node.try_get_context('glue_job_script_file_name')
    glue_job_input_arguments = self.node.try_get_context('glue_job_input_arguments')
    glue_job_default_arguments = {
      "--TempDir": "s3://{glue_assets}/temporary/".format(glue_assets=glue_assets_s3_bucket_name),
      "--enable-continuous-cloudwatch-log": "true",
      "--enable-glue-datacatalog": "true",
      "--enable-job-insights": "true",
      "--enable-metrics": "true",
      "--enable-spark-ui": "true",
      "--job-bookmark-option": "job-bookmark-enable",
      "--job-language": "python",
      "--spark-event-logs-path": "s3://{glue_assets}/sparkHistoryLogs/".format(
        glue_assets=glue_assets_s3_bucket_name)
    }

    glue_job_default_arguments.update(glue_job_input_arguments)

    glue_connections_name = self.node.try_get_context('glue_connections_name')

    glue_job_name = self.node.try_get_context('glue_job_name')

    glue_cfn_job = aws_glue.CfnJob(self, "GlueETLJob",
      command=aws_glue.CfnJob.JobCommandProperty(
        name="glueetl",
        python_version="3",
        script_location="s3://{glue_assets}/scripts/{glue_job_script_file_name}".format(
          glue_assets=glue_assets_s3_bucket_name,
          glue_job_script_file_name=glue_job_script_file_name
        )
      ),
      role=glue_job_role.role_arn,

      # the properties below are optional
      #XXX: Set only AllocatedCapacity or MaxCapacity
      # Do not set Allocated Capacity if using Worker Type and Number of Workers
      # allocated_capacity=2,
      connections=aws_glue.CfnJob.ConnectionsListProperty(
        connections=[glue_connections_name]
      ),
      default_arguments=glue_job_default_arguments,
      description="This job loads the data from employee_details dataset and creates the Iceberg Table.",
      execution_property=aws_glue.CfnJob.ExecutionPropertyProperty(
        max_concurrent_runs=1
      ),
      glue_version="3.0",
      #XXX: Do not set Max Capacity if using Worker Type and Number of Workers
      # max_capacity=2,
      max_retries=0,
      name=glue_job_name,
      # notification_property=aws_glue.CfnJob.NotificationPropertyProperty(
      #   notify_delay_after=10 # 10 minutes
      # ),
      number_of_workers=2,
      timeout=2880,
      worker_type="G.1X" # ['Standard' | 'G.1X' | 'G.2X' | 'G.025x']
    )

    cdk.CfnOutput(self, '{}_GlueJobName'.format(self.stack_name), value=glue_cfn_job.name,
      export_name='GlueJobName')
    cdk.CfnOutput(self, '{}_GlueJobRoleArn'.format(self.stack_name), value=glue_job_role.role_arn,
      export_name='GlueJobRoleArn')


app = cdk.App()
GlueJobStack(app, "GlueETLJobStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
