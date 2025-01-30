#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_autoscaling as autoscaling,
  aws_ec2,
  aws_ecs,
  aws_elasticloadbalancingv2 as elbv2,
  aws_iam
)

from constructs import Construct


class ECSClusterStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:

    super().__init__(scope, construct_id, **kwargs)

    # Create ECS cluster in the VPC
    cluster_name = self.node.try_get_context('ecs_cluster_name') or "awsvpc-ecs-demo"
    self.ecs_cluster = aws_ecs.Cluster(self, "ECSCluster",
      cluster_name=cluster_name,
      vpc=vpc
    )

    auto_scaling_group_settings = self.node.try_get_context('auto_scaling_group') or {}
    DESIRED_CAPACITY = auto_scaling_group_settings.get('desired_capacity', 1)
    MIN_CAPACITY = min(auto_scaling_group_settings.get('min_capacity', 1), DESIRED_CAPACITY)
    MAX_CAPACITY = max(auto_scaling_group_settings.get('max_capacity', 3), DESIRED_CAPACITY)

    # Create Auto Scaling Group for ECS cluster using launchtemplates
    # Uses t3.medium instances with Amazon Linux 2 ECS-optimized AMI
    asg = autoscaling.AutoScalingGroup(self, "DefaultAutoScalingGroup",
      vpc=vpc,
      launch_template=aws_ec2.LaunchTemplate(self, "LaunchTemplate",
        instance_type=aws_ec2.InstanceType.of(
          aws_ec2.InstanceClass.BURSTABLE3,
          aws_ec2.InstanceSize.MEDIUM),
        machine_image=aws_ecs.EcsOptimizedImage.amazon_linux2023(),
        user_data=aws_ec2.UserData.for_linux(),
        role=aws_iam.Role(self, "LaunchTemplateRole",
          assumed_by=aws_iam.ServicePrincipal("ec2.amazonaws.com")
        )
      ),
      desired_capacity=DESIRED_CAPACITY,
      min_capacity=MIN_CAPACITY,
      max_capacity=MAX_CAPACITY
    )
    asg.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    # Create and add capacity provider to the cluster
    capacity_provider = aws_ecs.AsgCapacityProvider(self, "AsgCapacityProvider",
      auto_scaling_group=asg
    )
    self.ecs_cluster.add_asg_capacity_provider(capacity_provider)


    cdk.CfnOutput(self, 'ClusterName',
      value=self.ecs_cluster.cluster_name,
      export_name=f'{self.stack_name}-ClusterName')
    cdk.CfnOutput(self, 'ClusterArn',
      value=self.ecs_cluster.cluster_arn,
      export_name=f'{self.stack_name}-ClusterArn')
