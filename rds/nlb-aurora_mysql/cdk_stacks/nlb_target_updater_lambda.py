#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_events,
  aws_events_targets,
  aws_iam,
  aws_lambda,
)
from constructs import Construct


class NLBTargetUpdaterLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, db_cluster, nlb_target_group, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    update_lambda = aws_lambda.Function(self, "UpdateNLBTargetLambda",
      runtime=aws_lambda.Runtime.PYTHON_3_11,
      handler="nlb_target_updater.lambda_handler",
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/python')),
      environment={
        "TARGET_GROUP_ARN": nlb_target_group.target_group_arn,
        "CLUSTER_ENDPOINT": db_cluster.cluster_endpoint.hostname,
        "CLUSTER_ENDPOINT_PORT": str(db_cluster.cluster_endpoint.port)
      },
      timeout=cdk.Duration.minutes(5)
    )

    update_lambda.add_to_role_policy(aws_iam.PolicyStatement(
      actions=[
        "elasticloadbalancing:DescribeTargetHealth",
        "elasticloadbalancing:RegisterTargets",
        "elasticloadbalancing:DeregisterTargets"
      ],
      resources=["*"]
    ))

    rds_failover_rule = aws_events.Rule(self, "RDSClusterFailoverRule",
      event_pattern=aws_events.EventPattern(
        source=["aws.rds"],
        detail_type=["RDS DB Cluster Event"],
        detail={
          "EventCategories": ["failover", "failure"],
          "SourceType": ["CLUSTER"]
        }
      )
    )

    rds_failover_rule.add_target(aws_events_targets.LambdaFunction(update_lambda))
