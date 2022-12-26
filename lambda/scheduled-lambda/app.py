#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_lambda,
  aws_events,
  aws_events_targets,
)
from constructs import Construct
from cdk_lambda_powertools_python_layer import LambdaPowertoolsLayer

class ScheduledLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    #vpc_name = self.node.try_get_context('vpc_name')
    #vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
    #  is_default=True,
    #  vpc_name=vpc_name
    #)

    # vpc = aws_ec2.Vpc(self, 'LambdaLayersVPC',
    #   max_azs=3,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )

    powertools_layer = LambdaPowertoolsLayer(self, 'PowertoolsLayer')

    lambda_fn = aws_lambda.Function(self, "ScheduledLambdaTest",
      runtime=aws_lambda.Runtime.PYTHON_3_7,
      function_name="ScheduledLambdaTest",
      handler="scheduled_lambda_test.lambda_handler",
      description="Scheduled Lambda Test",
      code=aws_lambda.Code.from_asset("./src/main/python"),
      timeout=cdk.Duration.minutes(5),
      layers=[powertools_layer]
      #vpc=vpc
    )

    # Create EventBridge rule that will execute our Lambda every 2 minutes
    schedule = aws_events.Rule(self, 'ScheduledLambdaTest-schedule',
      schedule=aws_events.Schedule.expression('rate(2 minutes)')
    )

    #Set the target of our EventBridge rule to our Lambda function
    schedule.add_target(aws_events_targets.LambdaFunction(lambda_fn))

app = cdk.App()
ScheduledLambdaStack(app, "ScheduledLambdaStack",  env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
