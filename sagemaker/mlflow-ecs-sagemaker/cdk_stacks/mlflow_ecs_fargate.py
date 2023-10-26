#!/usr/bin/env python3
import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_ecs,
  aws_ecr,
  aws_iam,
  aws_ecs_patterns,
)

from constructs import Construct


class MLflowECSFargateStack(Stack):

  def __init__(self, scope: Construct, construct_id: str,
    vpc,
    artifact_bucket,
    database_secret,
    database_name,
    **kwargs) -> None:

    super().__init__(scope, construct_id, **kwargs)

    ecs_cluster_config = self.node.try_get_context('ecs')
    ecs_cluster_name = ecs_cluster_config.get('cluster_name', 'mlflow')
    ecs_cluster = aws_ecs.Cluster(self, 'MLflowECSCluster',
      cluster_name=ecs_cluster_name,
      vpc=vpc
    )

    task_role = aws_iam.Role(self, 'MLflowECSFargateTaskRole',
      assumed_by=aws_iam.ServicePrincipal(service="ecs-tasks.amazonaws.com"),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonECS_FullAccess')
      ]
    )

    task_definition = aws_ecs.FargateTaskDefinition(self, "MLflowFargateTaskDef",
      task_role=task_role,
      cpu=4*1024,
      memory_limit_mib=8*1024,
    )

    container_info = self.node.try_get_context('container')
    container_repo_name = container_info.get('repository_name', 'mlflow')
    container_repo_arn = aws_ecr.Repository.arn_for_local_repository(container_repo_name,
      self, cdk.Aws.ACCOUNT_ID)

    # container_repository = aws_ecr.Repository.from_repository_arn(self, "ContainerRepository",
    #   repository_arn=repository_arn)
    #
    # jsii.errors.JSIIError: "repositoryArn" is a late-bound value,
    # and therefore "repositoryName" is required. Use `fromRepositoryAttributes` instead
    container_repository = aws_ecr.Repository.from_repository_attributes(self, "ContainerRepository",
      repository_arn=container_repo_arn,
      repository_name=container_repo_name)

    container_image_tag = container_info.get('image_tag', 'latest')
    container = task_definition.add_container('TaskContainer',
      image=aws_ecs.ContainerImage.from_ecr_repository(container_repository, tag=container_image_tag),
      environment={
        "BUCKET": f"s3://{artifact_bucket.bucket_name}",
        "DATABASE": database_name
      },
      secrets={
        "HOST": aws_ecs.Secret.from_secrets_manager(database_secret, 'host'),
        "PORT": aws_ecs.Secret.from_secrets_manager(database_secret, 'port'),
        "USERNAME": aws_ecs.Secret.from_secrets_manager(database_secret, 'username'),
        "PASSWORD": aws_ecs.Secret.from_secrets_manager(database_secret, 'password')
      },
      logging=aws_ecs.LogDriver.aws_logs(stream_prefix="mlflow"),
    )

    port_mapping = aws_ecs.PortMapping(
      container_port=5000,
      host_port=5000,
      protocol=aws_ecs.Protocol.TCP
    )
    container.add_port_mappings(port_mapping)

    service_name = ecs_cluster_config.get('service_name', 'mlflow')
    fargate_service = aws_ecs_patterns.NetworkLoadBalancedFargateService(self, 'MLflowNLBFargateService',
      service_name=service_name,
      cluster=ecs_cluster,
      task_definition=task_definition,
    )

    # Setup security group
    fargate_service.service.connections.security_groups[0].add_ingress_rule(
      peer=aws_ec2.Peer.ipv4(vpc.vpc_cidr_block),
      connection=aws_ec2.Port.tcp(5000),
      description="Allow inbound from VPC for mlflow",
    )

    # Setup autoscaling policy
    scaling = fargate_service.service.auto_scale_task_count(max_capacity=2)
    scaling.scale_on_cpu_utilization(
      'ECSFargateAutoScaling',
      target_utilization_percent=70,
      scale_in_cooldown=cdk.Duration.seconds(60),
      scale_out_cooldown=cdk.Duration.seconds(60),
    )

    cdk.CfnOutput(self, 'MLflowTrakingURI',
      value=fargate_service.load_balancer.load_balancer_dns_name,
      export_name=f'{self.stack_name}-MLflowTrakingURI'
    )
