import aws_cdk as cdk

from aws_cdk import (
  Stack,
)
from constructs import Construct

class CustomResourceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, cr_provider_lambda_arn, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    cdk.CustomResource(self, "MyCustomResource",
      service_token=cr_provider_lambda_arn)
