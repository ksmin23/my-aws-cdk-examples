#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_elasticloadbalancingv2 as elbv2,
  aws_elasticloadbalancingv2_targets as elbv2_targets,
  aws_lambda,
)
from constructs import Construct


class AlbPathRoutingLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # The code that defines your stack goes here
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
    vpc_name = self.node.try_get_context('vpc_name')
    vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
      is_default=True,
      vpc_name=vpc_name
    )

    # vpc = aws_ec2.Vpc(self, "AlbLambdaStackVPC",
    #   max_azs=3,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )

    lambda_fn1 = aws_lambda.Function(self, "AlbTargetLambdaFunction1",
      runtime=aws_lambda.Runtime.PYTHON_3_9,
      function_name="Hello-World",
      handler="index.lambda_handler",
      description="Lambda function triggerred by Application Load Balancer",
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), 'src/main/python')),
      environment={
        "MESSAGE": "Hello"
      },
      timeout=cdk.Duration.minutes(5)
    )

    lambda_fn2 = aws_lambda.Function(self, "AlbTargetLambdaFunction2",
      runtime=aws_lambda.Runtime.PYTHON_3_9,
      function_name="Aloha-World",
      handler="index.lambda_handler",
      description="Lambda function triggerred by Application Load Balancer",
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), 'src/main/python')),
      environment={
        "MESSAGE": "Aloha"
      },
      timeout=cdk.Duration.minutes(5)
    )

    lb = elbv2.ApplicationLoadBalancer(self, "ALB",
      vpc=vpc,
      internet_facing=True
    )

    alb_tg = elbv2.ApplicationTargetGroup(self, "ALBTargetGroup",
      # target_type=elbv2.TargetType.INSTANCE,
      port=80,
      stickiness_cookie_duration=cdk.Duration.minutes(5),
      vpc=vpc
    )

    listener_http = lb.add_listener("HTTPListener",
      port=80,
      # 'open: true' is the default, you can leave it out if you want. Set it
      # to 'false' and use `listener.connections` if you want to be selective
      # about who can access the load balancer.
      open=True
    )

    listener_http.add_target_groups("HTTPListenerTargetGroup",
      target_groups=[alb_tg]
    )
  
    listener_http.add_targets("HTTPListenerTarget1",
      # port/protocol should not be specified for Lambda targets
      priority=1,
      targets=[elbv2_targets.LambdaTarget(lambda_fn1)],
      conditions=[
        # elbv2.ListenerCondition.path_patterns(["/hello"])
        elbv2.ListenerCondition.path_patterns(["/hello", "/hello/*"])
      ],
      health_check=elbv2.HealthCheck(
        enabled=True
      ),
    )

    listener_http.add_targets("HTTPListenerTarget2",
      # port/protocol should not be specified for Lambda targets
      priority=2,
      targets=[elbv2_targets.LambdaTarget(lambda_fn2)],
      conditions=[
        # elbv2.ListenerCondition.path_patterns(["/aloha"])
        elbv2.ListenerCondition.path_patterns(["/aloha", "/aloha/*"])
      ],
      health_check=elbv2.HealthCheck(
        enabled=True
      ),
    )

    # lb.add_redirect(
    #   source_port=8080,
    #   source_protocol=elbv2.ApplicationProtocol.HTTP,
    #   target_port=80,
    #   target_protocol=elbv2.ApplicationProtocol.HTTP
    # )

    cdk.CfnOutput(self, 'ALB_DNS_Name', value=lb.load_balancer_dns_name)
    cdk.CfnOutput(self, 'ALB_URL', value=f'http://{lb.load_balancer_dns_name}')


app = cdk.App()
AlbPathRoutingLambdaStack(app, "AlbPathRoutingLambdaStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
