import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_glue,
  aws_iam,
  aws_s3 as s3,
)
from constructs import Construct

class GlueStreamingJobStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    glue_job_role_policy_doc = aws_iam.PolicyDocument()

    glue_job_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "S3Access",
      "effect": aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": ["*"],
      "actions": [
        "s3:GetBucketLocation",
        "s3:ListBucket",
        "s3:GetBucketAcl",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:PutObject",
        "s3:DeleteObject"
      ]
    }))

    glue_job_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "CloudWatchLogsAccess",
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:PutLogEvents",
      ]
    }))

    glue_job_role = aws_iam.Role(self, 'GlueStreamingJobRole',
      role_name='GlueStreamingJobRole',
      assumed_by=aws_iam.ServicePrincipal('glue.amazonaws.com'),
      inline_policies={
        'aws_glue_job_role_policy': glue_job_role_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSGlueServiceRole'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMReadOnlyAccess'),
        # aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonEC2ContainerRegistryReadOnly'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AWSGlueConsoleFullAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonKinesisReadOnlyAccess'),
        # aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
        # aws_iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsFullAccess'), #TODO: need to be refined
        # aws_iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsReadOnlyAccess')
      ]
    )

    #XXX: When creating a notebook with a role, that role is then passed to interactive sessions
    # so that the same role can be used in both places.
    # As such, the `iam:PassRole` permission needs to be part of the role's policy.
    # More info at: https://docs.aws.amazon.com/glue/latest/ug/notebook-getting-started.html
    #
    glue_job_role.add_to_policy(aws_iam.PolicyStatement(**{
      "sid": "AWSGlueJobIAMPassRole",
      "effect": aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [self.format_arn(service="iam", region="", resource="role", resource_name=glue_job_role.role_name)],
      "conditions": {
        "StringLike": {
          "iam:PassedToService": [
            "glue.amazonaws.com"
          ]
        }
      },
      "actions": [
        "iam:PassRole"
      ]
    }))

    glue_assets_s3_bucket_name = self.node.try_get_context('glue_assets_s3_bucket_name')
    glue_job_script_file_name = self.node.try_get_context('glue_job_script_file_name')
    glue_job_input_arguments = self.node.try_get_context('glue_job_input_arguments')

    glue_job_default_arguments = {
      "--enable-metrics": "true",
      "--enable-spark-ui": "true",
      "--spark-event-logs-path": f"s3://{glue_assets_s3_bucket_name}/sparkHistoryLogs/",
      "--enable-job-insights": "false",
      "--enable-glue-datacatalog": "true",
      "--enable-continuous-cloudwatch-log": "true",
      "--job-bookmark-option": "job-bookmark-disable",
      "--job-language": "python",
      "--TempDir": f"s3://{glue_assets_s3_bucket_name}/temporary/"
    }

    glue_job_default_arguments.update(glue_job_input_arguments)

    glue_job_name = self.node.try_get_context('glue_job_name')

    glue_cfn_job = aws_glue.CfnJob(self, "GlueStreamingETLJob",
      command=aws_glue.CfnJob.JobCommandProperty(
        name="gluestreaming",
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
      default_arguments=glue_job_default_arguments,
      description="This job loads the data from employee_details dataset and creates the Iceberg Table.",
      execution_property=aws_glue.CfnJob.ExecutionPropertyProperty(
        max_concurrent_runs=1
      ),
      #XXX: check AWS Glue Version in https://docs.aws.amazon.com/glue/latest/dg/add-job.html#create-job
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
