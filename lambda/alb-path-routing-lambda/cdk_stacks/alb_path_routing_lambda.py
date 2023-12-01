#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_elasticloadbalancingv2 as elbv2,
  aws_elasticloadbalancingv2_targets as elbv2_targets,
  aws_lambda,
)
from constructs import Construct


class AlbPathRoutingLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    lambda_fn1 = aws_lambda.Function(self, "AlbTargetLambdaFunction1",
      runtime=aws_lambda.Runtime.PYTHON_3_9,
      function_name="Hello-World",
      handler="index.lambda_handler",
      description='An Application Load Balancer Lambda Target that returns "Hello World"',
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/python')),
      environment={
        "MESSAGE": "Hello"
      },
      timeout=cdk.Duration.minutes(5)
    )

    lambda_fn2 = aws_lambda.Function(self, "AlbTargetLambdaFunction2",
      runtime=aws_lambda.Runtime.PYTHON_3_9,
      function_name="Aloha-World",
      handler="index.lambda_handler",
      description='An Application Load Balancer Lambda Target that returns "Aloha World"',
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/python')),
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
      # [Warning] When creating an empty TargetGroup, you should specify a 'targetType' (this warning may become an error in the future)
      target_type=elbv2.TargetType.LAMBDA,
      # [Error] port/protocol should not be specified for Lambda targets
      # port=80,
      # [Error] A target group with target type 'lambda' does not support the attribute stickiness.lb_cookie.duration_seconds
      # stickiness_cookie_duration=cdk.Duration.minutes(5),
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
        elbv2.ListenerCondition.path_patterns(["/", "/hello", "/hello/*"])
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
        elbv2.ListenerCondition.path_patterns(["/aloha", "/aloha/*"])
      ],
      health_check=elbv2.HealthCheck(
        enabled=True
      ),
    )


    cdk.CfnOutput(self, 'ALB_DNS_Name',
      value=lb.load_balancer_dns_name,
      export_name=f'{self.stack_name}-ALB-DNS-Name')
    cdk.CfnOutput(self, 'ALB_URL',
      value=f'http://{lb.load_balancer_dns_name}',
      export_name=f'{self.stack_name}-ALBURL')
