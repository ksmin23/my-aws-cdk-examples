import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam
)
from constructs import Construct


class OpsCollectionPipelineRoleStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    collection_pipeline_policy_doc = aws_iam.PolicyDocument()

    collection_pipeline_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "aoss:BatchGetCollection"
      ]
    }))

    pipeline_role = aws_iam.Role(self, 'OpenSearchIngestionPipelineRole',
      role_name='OpenSearchCollectionPipelineRole',
      assumed_by=aws_iam.ServicePrincipal('osis-pipelines.amazonaws.com'),
      inline_policies={
        'collection-pipeline-policy': collection_pipeline_policy_doc
      }
    )
    self.iam_role = pipeline_role

    cdk.CfnOutput(self, f'{self.stack_name}_Role', value=self.iam_role.role_name)
    cdk.CfnOutput(self, f'{self.stack_name}_RoleArn', value=self.iam_role.role_arn)