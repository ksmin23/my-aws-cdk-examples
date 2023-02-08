#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_lambda,
  aws_ecr,
)

from constructs import Construct


class LambdaCustomContainerStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    # if you encounter an error such as:
    #  jsii.errors.JavaScriptError:
    #    Error: When providing vpc options you need to provide a subnet for each AZ you are using at new Domain
    # check https://github.com/aws/aws-cdk/issues/12078
    # This error occurs when ZoneAwarenessEnabled in aws_opensearch.Domain(..) is set `true`
    # 
    # vpc_name = self.node.try_get_context('vpc_name')
    # vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
    #   is_default=True,
    #   vpc_name=vpc_name
    # )

    vpc = aws_ec2.Vpc(self, "LambdaCustomContainerVPC",
      max_azs=3,
      gateway_endpoints={
        "S3": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.S3
        )
      }
    )

    ecr_repo_name = self.node.try_get_context('ecr_repo_name')
    custom_container_ecr_repo = aws_ecr.Repository.from_repository_name(self,
      "LambdaCustomContainerEcrRepo", repository_name=ecr_repo_name)

    lambda_fn = aws_lambda.Function(self, "CustomContainerLambdaFunction",
      code=aws_lambda.Code.from_ecr_image(repository=custom_container_ecr_repo,
        # The image tag or digest to use when pulling the image from ECR (digests must start with sha256:)
        tag_or_digest='latest' # default: 'latest'
      ),
      #XXX: handler must be `Handler.FROM_IMAGE` when using image asset for Lambda function
      handler=aws_lambda.Handler.FROM_IMAGE,
      #XXX: runtime must be `Runtime.FROM_IMAGE` when using image asset for Lambda function
      runtime=aws_lambda.Runtime.FROM_IMAGE,
      function_name="Hello-KoNLpy",
      description="Lambda function defined in the custom container",
      timeout=cdk.Duration.minutes(5),
      memory_size=5120
    )


app = cdk.App()
LambdaCustomContainerStack(app, "LambdaCustomContainerStack",
  env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
