#!/usr/bin/env python3
import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_ecs,
  aws_elasticloadbalancingv2 as aws_elbv2,
  aws_iam,
)

from constructs import Construct


class MLflowECSFargateStack(Stack):

  def __init__(self, scope: Construct, construct_id: str,
    vpc,
    artifact_bucket,
    sg_rds_client,
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
      memory_limit_mib=8*1024
    )

    container = task_definition.add_container('TaskContainer',
      image=aws_ecs.ContainerImage.from_asset(directory="container",
        asset_name="mlflow"),
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


    sg_fargate_service = aws_ec2.SecurityGroup(self, 'FargateServiceSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='ECS Fargate Service Security Group for MLflow',
      security_group_name='mlflow-ecs-fargate-service-sg'
    )

    sg_fargate_service.add_ingress_rule(
      peer=aws_ec2.Peer.ipv4(vpc.vpc_cidr_block),
      connection=aws_ec2.Port.tcp(5000),
      description="Allow inbound from VPC for mlflow",
    )
    cdk.Tags.of(sg_fargate_service).add('Name', 'mlflow-ecs-fargate-service-sg')

    service_name = ecs_cluster_config.get('service_name', 'mlflow')
    fargate_service = aws_ecs.FargateService(self, "MLflowFargateService",
      service_name=service_name,
      cluster=ecs_cluster,
      task_definition=task_definition,
      security_groups=[sg_fargate_service, sg_rds_client],
    )

    scalalbe_task_count = fargate_service.auto_scale_task_count(max_capacity=2)
    scalalbe_task_count.scale_on_cpu_utilization(
      'ECSFargateAutoScaling',
      target_utilization_percent=70,
      scale_in_cooldown=cdk.Duration.seconds(60),
      scale_out_cooldown=cdk.Duration.seconds(60),
    )

    nlb = aws_elbv2.NetworkLoadBalancer(self, "LB",
      vpc=vpc,
      internet_facing=True
    )

    listener = nlb.add_listener("PublicListener",
      port=80
    )

    target_group = listener.add_targets("ECS",
      port=80,
      targets=[fargate_service]
    )

    cdk.CfnOutput(self, 'MLflowTrakingURI',
      value=nlb.load_balancer_dns_name,
      export_name=f'{self.stack_name}-MLflowTrakingURI'
    )
