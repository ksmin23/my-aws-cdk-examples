#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_ecs,
  aws_ecs_patterns,
  aws_iam,
)

from constructs import Construct


class ECSAlbFargateServiceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str,
    vpc,
    ecs_cluster,
    ecr_repositories,
    load_balancer,
    sg_efs_inbound,
    efs_file_system,
    **kwargs) -> None:

    super().__init__(scope, construct_id, **kwargs)

    task_execution_role_policy_doc = aws_iam.PolicyDocument()
    task_execution_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
    }))

    task_execution_role = aws_iam.Role(self, "ECSTaskExecutionRole",
      role_name=f'ECSTaskExecutionRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal(service="ecs-tasks.amazonaws.com"),
      inline_policies={
        'ecs_task_execution_role_policy': task_execution_role_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
      ]
    )

    task_role_policy_doc = aws_iam.PolicyDocument()
    task_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "elasticfilesystem:ClientMount",
        "elasticfilesystem:ClientWrite",
      ]
    }))

    task_role = aws_iam.Role(self, "ECSTaskRole",
      role_name=f'ECSTaskRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal(service="ecs-tasks.amazonaws.com"),
      inline_policies={
        'ecs_task_role_policy': task_role_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"),
        # aws_iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess"),
        # aws_iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite")
      ]
    )

    efs_volume = aws_ecs.Volume(
      name="uploads",
      efs_volume_configuration=aws_ecs.EfsVolumeConfiguration(
        file_system_id=efs_file_system.file_system_id,
        root_directory="/"
      )
    )

    ecs_task_definition = aws_ecs.FargateTaskDefinition(self, "ECSTaskDefinition",
      cpu=1*256,
      memory_limit_mib=512,
      execution_role=task_execution_role,
      task_role=task_role,
      volumes=[efs_volume]
    )

    repository = ecr_repositories['cloudcmd']
    container = ecs_task_definition.add_container("ECSContainerDefinition",
      image=aws_ecs.ContainerImage.from_ecr_repository(repository, tag="latest"),
      port_mappings=[
        aws_ecs.PortMapping(
          container_port=8000,
          host_port=8000,
          protocol=aws_ecs.Protocol.TCP
        )
      ]
    )

    mount_point = aws_ecs.MountPoint(
      container_path="/uploads",
      read_only=False,
      source_volume="uploads"
    )
    container.add_mount_points(mount_point)

    service_name = self.node.try_get_context('ecs_service_name') or "cloudcmd"

    sg_fargate_service = aws_ec2.SecurityGroup(self, 'ECSFargateServiceSG',
      vpc=vpc,
      allow_all_outbound=True,
      description="Allow inbound from VPC for ECS Fargate Service",
      security_group_name=f'{service_name}-ecs-service-sg'
    )
    sg_fargate_service.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(8000))
    cdk.Tags.of(sg_fargate_service).add('Name', 'fargate-service-with-efs')

    fargate_service = aws_ecs_patterns.ApplicationLoadBalancedFargateService(self, "ALBFargateService",
      service_name=service_name,
      cluster=ecs_cluster,
      desired_count=2,
      min_healthy_percent=50,
      task_definition=ecs_task_definition,
      load_balancer=load_balancer,
      security_groups=[sg_fargate_service, sg_efs_inbound]
    )
    fargate_service.target_group.set_attribute('deregistration_delay.timeout_seconds', '30')
    cdk.Tags.of(fargate_service).add('Name', 'fargate-service-with-efs')

    efs_file_system.grant_root_access(fargate_service.task_definition.task_role.grant_principal)


    cdk.CfnOutput(self, "LoadBalancerDNS",
      value=f'http://{fargate_service.load_balancer.load_balancer_dns_name}',
      export_name=f'{self.stack_name}-LoadBalancerDNS')
    cdk.CfnOutput(self, 'TaskDefinitionArn',
      value=ecs_task_definition.task_definition_arn,
      export_name=f'{self.stack_name}-TaskDefinitionArn')
