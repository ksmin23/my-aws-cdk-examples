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

class AlbLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    lambda_fn = aws_lambda.Function(self, "AlbTargetLambdaFunction",
      runtime=aws_lambda.Runtime.PYTHON_3_9,
      function_name="ALBTargetLambda",
      handler="index.lambda_handler",
      description="Lambda function triggerred by Application Load Balancer",
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/python')),
      timeout=cdk.Duration.minutes(5)
    )

    lb = elbv2.ApplicationLoadBalancer(self, "ALB",
      vpc=vpc,
      internet_facing=True
    )

    listener_http = lb.add_listener("HTTPListener",
      port=80,

      # 'open: true' is the default, you can leave it out if you want. Set it
      # to 'false' and use `listener.connections` if you want to be selective
      # about who can access the load balancer.
      open=True
    )

    listener_http.add_targets("HTTPListenerTargets",
      targets=[elbv2_targets.LambdaTarget(lambda_fn)],
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
