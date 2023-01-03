#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_batch,
  aws_iam
)
from constructs import Construct

class BatchWithEC2Stack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    vpc_name = self.node.try_get_context('vpc_name')
    vpc = aws_ec2.Vpc.from_lookup(self, 'BatchWithEC2StackVPC',
      is_default=True, # set is_default=False if you want to find your own VPC
      vpc_name=vpc_name)

    sg_batch_instance = aws_ec2.SecurityGroup(self, 'BatchInstanceSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='default security group for batch instance',
      security_group_name='batch-instance-sg'
    )
    cdk.Tags.of(sg_batch_instance).add('Name', 'batch-instance-sg')

    ecs_instance_role = aws_iam.Role(self, 'BatchECSInstanceRole',
      role_name='ecsInstanceRoleForBatch',
      assumed_by=aws_iam.ServicePrincipal('ec2.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonEC2ContainerServiceforEC2Role'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore')
      ]
    )

    ecs_instance_profile_role = aws_iam.CfnInstanceProfile(self, 'BatchECSInstanceProfileRole',
      instance_profile_name='ecsInstanceRoleForBatch',
      roles=[ecs_instance_role.role_name]
    )

    batch_service_role = aws_iam.Role(self, 'BatchServiceRole',
      role_name='AWSBatchServiceRole',
      assumed_by=aws_iam.ServicePrincipal('batch.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSBatchServiceRole')
      ]
    )

    batch_compute_env = aws_batch.CfnComputeEnvironment(self, 'BatchComputeEnv',
      type='MANAGED',

      # the properties below are optional
      compute_environment_name='batch-compute-env',
      compute_resources=aws_batch.CfnComputeEnvironment.ComputeResourcesProperty(
        maxv_cpus=32,
        subnets=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
        type='EC2',

        # the properties below are optional
        allocation_strategy='BEST_FIT',
        desiredv_cpus=0,
        minv_cpus=0,
        ec2_configuration=[aws_batch.CfnComputeEnvironment.Ec2ConfigurationObjectProperty(
          image_type='ECS_AL2'
        )],
        instance_role=ecs_instance_profile_role.attr_arn,
        instance_types=['optimal'],
        security_group_ids=[sg_batch_instance.security_group_id]
      ),
      service_role=batch_service_role.role_arn,
      state='ENABLED'
    )
    batch_compute_env.add_dependency(ecs_instance_profile_role)

    batch_job_queue = aws_batch.CfnJobQueue(self, 'BatchJobQueue',
      compute_environment_order=[aws_batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
        compute_environment=batch_compute_env.ref,
        order=1
      )],
      priority=1,

      # the properties below are optional
      job_queue_name='batch-job-queue',
      state='ENABLED'
    )
    batch_job_queue.add_dependency(batch_compute_env)


app = cdk.App()
BatchWithEC2Stack(app, 'BatchWithEC2Stack', env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
