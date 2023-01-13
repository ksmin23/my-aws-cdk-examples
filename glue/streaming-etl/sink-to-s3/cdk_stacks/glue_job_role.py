import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam
)
from constructs import Construct


class GlueJobRoleStack(Stack):

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
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AWSGlueConsoleFullAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonKinesisReadOnlyAccess')
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

    self.glue_job_role = glue_job_role

    cdk.CfnOutput(self, f'{self.stack_name}_GlueJobRole', value=self.glue_job_role.role_name)
    cdk.CfnOutput(self, f'{self.stack_name}_GlueJobRoleArn', value=self.glue_job_role.role_arn)
