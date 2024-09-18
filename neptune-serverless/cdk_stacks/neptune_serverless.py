#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_neptune
)
from constructs import Construct


class NeptuneServerlessStack(Stack):

  def __init__(self, scope: Construct, id: str, vpc, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    neptune_load_from_s3_policy_doc = aws_iam.PolicyDocument()
    neptune_load_from_s3_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "NeptuneLoadFromS3",
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "s3:Get*",
        "s3:List*"
      ]
    }))

    neptune_load_from_s3_role = aws_iam.Role(self, 'NeptuneLoadFromS3Role',
      role_name=f'NeptuneLoadFromS3Role-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('rds.amazonaws.com'),
      inline_policies={
        'NeptuneLoadFromS3Policy': neptune_load_from_s3_policy_doc
      }
    )

    neptune_ml_policy_doc = aws_iam.PolicyDocument()
    neptune_ml_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "ec2:CreateNetworkInterface",
        "ec2:CreateNetworkInterfacePermission",
        "ec2:CreateVpcEndpoint",
        "ec2:DeleteNetworkInterface",
        "ec2:DeleteNetworkInterfacePermission",
        "ec2:DescribeDhcpOptions",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeRouteTables",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcEndpoints",
        "ec2:DescribeVpcs"
      ]
    }))

    neptune_ml_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:ecr:*:*:repository/*"],
      "actions": [
        "ecr:GetAuthorizationToken",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability"
      ]
    }))

    neptune_ml_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:ecr:*:*:repository/*"],
      "actions": [
        "iam:PassRole"
      ],
      "conditions": {
        "StringEquals": {
          "iam:PassedToService": [
            "sagemaker.amazonaws.com"
          ]
        }
      }
    }))

    neptune_ml_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:kms:*:*:key/*"],
      "actions": [
        "kms:CreateGrant",
        "kms:Decrypt",
        "kms:GenerateDataKey*"
      ]
    }))

    neptune_ml_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:logs:*:*:log-group:/aws/sagemaker/*"],
      "actions": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
    }))

    neptune_ml_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:sagemaker:*:*:*"],
      "actions": [
        "sagemaker:CreateEndpoint",
        "sagemaker:CreateEndpointConfig",
        "sagemaker:CreateHyperParameterTuningJob",
        "sagemaker:CreateModel",
        "sagemaker:CreateProcessingJob",
        "sagemaker:CreateTrainingJob",
        "sagemaker:DeleteEndpoint",
        "sagemaker:DeleteEndpointConfig",
        "sagemaker:StopHyperParameterTuningJob",
        "sagemaker:DeleteModel",
        "sagemaker:StopProcessingJob",
        "sagemaker:StopTrainingJob",
        "sagemaker:DescribeEndpoint",
        "sagemaker:DescribeEndpointConfig",
        "sagemaker:DescribeHyperParameterTuningJob",
        "sagemaker:DescribeModel",
        "sagemaker:DescribeProcessingJob",
        "sagemaker:DescribeTrainingJob",
        "sagemaker:InvokeEndpoint",
        "sagemaker:ListTags",
        "sagemaker:AddTags",
        "sagemaker:ListTrainingJobsForHyperParameterTuningJob",
        "sagemaker:UpdateEndpoint",
        "sagemaker:UpdateEndpointWeightsAndCapacities"
      ]
    }))

    neptune_ml_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "sagemaker:ListEndpointConfigs",
        "sagemaker:ListEndpoints",
        "sagemaker:ListHyperParameterTuningJobs",
        "sagemaker:ListModels",
        "sagemaker:ListProcessingJobs",
        "sagemaker:ListTrainingJobs"
      ]
    }))

    neptune_ml_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:s3:::*"],
      "actions": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:AbortMultipartUpload",
        "s3:ListBucket"
      ]
    }))

    neptune_ml_role = aws_iam.Role(self, 'NeptuneMLRole',
      role_name=f'NeptuneMLRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('rds.amazonaws.com'),
      inline_policies={
        'NeptuneMLPolicy': neptune_ml_policy_doc
      }
    )

    neptune_ml_role.assume_role_policy.add_statements(aws_iam.PolicyStatement(**{
      "principals": [
        aws_iam.ServicePrincipal('sagemaker.amazonaws.com')
      ],
      "actions": [
        "sts:AssumeRole"
      ]
    }))

    self.sg_graph_db_client = aws_ec2.SecurityGroup(self, 'NeptuneClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for neptune client',
      security_group_name=f'neptune-client-sg-{self.stack_name.lower()}'
    )
    cdk.Tags.of(self.sg_graph_db_client).add('Name', 'neptune-client-sg')

    sg_graph_db = aws_ec2.SecurityGroup(self, 'NeptuneSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for neptune',
      security_group_name=f'neptune-sg-{self.stack_name.lower()}'
    )
    cdk.Tags.of(sg_graph_db).add('Name', 'neptune-server-sg')

    sg_graph_db.add_ingress_rule(peer=sg_graph_db, connection=aws_ec2.Port.tcp(8182), description='neptune-server-sg')
    sg_graph_db.add_ingress_rule(peer=self.sg_graph_db_client, connection=aws_ec2.Port.tcp(8182), description='neptune-client-sg')

    private_subnets = vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)
    availability_zones = private_subnets.availability_zones[:2]

    self.graph_db_subnet_group = aws_neptune.CfnDBSubnetGroup(self, 'NeptuneSubnetGroup',
      db_subnet_group_description='subnet group for neptune',
      subnet_ids=private_subnets.subnet_ids[:2],
      db_subnet_group_name=f'neptune-subnet-{self.stack_name}'
    )

    db_cluster_id = self.node.try_get_context('neptune_db_cluster_id') or 'neptune-serverless-demo'

    neptune_enable_audit_log = int(self.node.try_get_context('neptune_enable_audit_log') or '0')
    db_cluster_parameter_group = aws_neptune.CfnDBClusterParameterGroup(self, "NeptuneDBClusterParameterGroup",
      description="neptune db cluster parameter group",
      family="neptune1.3",
      parameters={
        'neptune_enable_audit_log': neptune_enable_audit_log,
        'neptune_ml_iam_role': neptune_ml_role.role_arn
      },
      name=f"{db_cluster_id}-db-cluster-params"
    )

    neptune_query_timeout = int(self.node.try_get_context('neptune_query_timeout') or '20000')
    db_instance_parameter_group = aws_neptune.CfnDBParameterGroup(self, "NeptuneDBInstanceParameterGroup",
      description="neptune db parameter group",
      family="neptune1.3",
      parameters={
        'neptune_query_timeout': neptune_query_timeout
      },
      name=f"{db_cluster_id}-db-params"
    )

    neptune_min_ncus = self.node.try_get_context('neptune_min_ncus') or 2.5
    neptune_max_ncus = self.node.try_get_context('neptune_max_ncus') or 128
    self.graph_db = aws_neptune.CfnDBCluster(self, 'NeptuneCluster',
      associated_roles=[
        aws_neptune.CfnDBCluster.DBClusterRoleProperty(
          role_arn=neptune_load_from_s3_role.role_arn
        ),
        aws_neptune.CfnDBCluster.DBClusterRoleProperty(
          role_arn=neptune_ml_role.role_arn
        )
      ],
      availability_zones=availability_zones,
      db_subnet_group_name=self.graph_db_subnet_group.db_subnet_group_name,
      db_cluster_identifier=db_cluster_id,
      db_cluster_parameter_group_name=db_cluster_parameter_group.name,
      db_instance_parameter_group_name=db_instance_parameter_group.name,
      backup_retention_period=1,
      preferred_backup_window='08:45-09:15',
      preferred_maintenance_window='sun:18:00-sun:18:30',
      serverless_scaling_configuration=aws_neptune.CfnDBCluster.ServerlessScalingConfigurationProperty(
        min_capacity=neptune_min_ncus,
        max_capacity=neptune_max_ncus
      ),
      vpc_security_group_ids=[sg_graph_db.security_group_id]
    )
    self.graph_db.add_dependency(self.graph_db_subnet_group)
    self.graph_db.add_dependency(db_cluster_parameter_group)
    self.graph_db.add_dependency(db_instance_parameter_group)

    db_instance_id = self.node.try_get_context('neptune_db_instance_id') or db_cluster_id
    graph_db_instance = aws_neptune.CfnDBInstance(self, 'NeptuneInstance',
      db_instance_class='db.serverless',
      allow_major_version_upgrade=False,
      auto_minor_version_upgrade=False,
      availability_zone=availability_zones[0],
      db_cluster_identifier=self.graph_db.db_cluster_identifier,
      db_instance_identifier=db_instance_id,
      db_parameter_group_name=db_instance_parameter_group.name,
      preferred_maintenance_window='sun:18:00-sun:18:30'
    )
    graph_db_instance.add_dependency(self.graph_db)

    db_replica_id_suffix = self.node.try_get_context('neptune_db_replica_id_suffix') or 'replica'
    graph_db_replica_instance = aws_neptune.CfnDBInstance(self, 'NeptuneReplicaInstance',
      db_instance_class='db.serverless',
      allow_major_version_upgrade=False,
      auto_minor_version_upgrade=False,
      availability_zone=availability_zones[-1],
      db_cluster_identifier=self.graph_db.db_cluster_identifier,
      db_instance_identifier=f'{db_instance_id}-{db_replica_id_suffix}',
      db_parameter_group_name=db_instance_parameter_group.name,
      preferred_maintenance_window='sun:18:00-sun:18:30'
    )
    graph_db_replica_instance.add_dependency(self.graph_db)
    graph_db_replica_instance.add_dependency(graph_db_instance)


    cdk.CfnOutput(self, 'NeptuneDBClusterId',
      value=self.graph_db.db_cluster_identifier,
      export_name=f'{self.stack_name}-DBClusterId')
    cdk.CfnOutput(self, 'NeptuneClusterEndpoint',
      value=self.graph_db.attr_endpoint,
      export_name=f'{self.stack_name}-Endpoint')
    cdk.CfnOutput(self, 'NeptuneClusterReadEndpoint',
      value=self.graph_db.attr_read_endpoint,
      export_name=f'{self.stack_name}-ReadEndpoint')
    cdk.CfnOutput(self, 'NeptuneClusterPort',
      value=self.graph_db.attr_port,
      export_name=f'{self.stack_name}-Port')
    cdk.CfnOutput(self, 'NeptuneClientSecurityGroupId',
      value=self.sg_graph_db_client.security_group_id,
      export_name=f'{self.stack_name}-ClientSecurityGroupId')
    cdk.CfnOutput(self, 'NeptuneLoadFromS3RoleArn',
      value=neptune_load_from_s3_role.role_arn,
      export_name=f'{self.stack_name}-NeptuneLoadFromS3RoleArn')
    cdk.CfnOutput(self, 'NeptuneMLRoleArn',
      value=neptune_ml_role.role_arn,
      export_name=f'{self.stack_name}-NeptuneMLRoleArn')
