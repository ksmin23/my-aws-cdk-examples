import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam
)
from constructs import Construct


class GlueStudioRoleStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    glue_notebook_role_policy_doc = aws_iam.PolicyDocument()

    glue_notebook_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
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

    glue_studio_role = aws_iam.Role(self, 'GlueStudioRole',
      role_name='AWSGlueServiceRole-StudioNotebook',
      assumed_by=aws_iam.ServicePrincipal('glue.amazonaws.com'),
      inline_policies={
        'aws_glue_notebook_role_policy': glue_notebook_role_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSGlueServiceRole'),
        # aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess')
      ]
    )

    #XXX: When creating a notebook with a role, that role is then passed to interactive sessions
    # so that the same role can be used in both places.
    # As such, the `iam:PassRole` permission needs to be part of the role's policy.
    # More info at: https://docs.aws.amazon.com/glue/latest/ug/notebook-getting-started.html
    #
    glue_studio_role.add_to_policy(aws_iam.PolicyStatement(**{
      "sid": "AWSGlueStudioIAMPassRole",
      "effect": aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [self.format_arn(service="iam", region="", resource="role", resource_name=glue_studio_role.role_name)],
      "actions": [
        "iam:PassRole"
      ]
    }))

    self.iam_role = glue_studio_role

    cdk.CfnOutput(self, f'{self.stack_name}_GlueStudioRole', value=self.iam_role.role_name)
    cdk.CfnOutput(self, f'{self.stack_name}_GlueStudioRoleArn', value=self.iam_role.role_arn)
