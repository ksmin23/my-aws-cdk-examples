#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_neptune
)
from constructs import Construct


class NeptuneStack(Stack):

  def __init__(self, scope: Construct, id: str, vpc, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    sg_graph_db_client = aws_ec2.SecurityGroup(self, "NeptuneClientSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for neptune client',
      security_group_name='neptune-client-sg'
    )
    cdk.Tags.of(sg_graph_db_client).add('Name', 'neptune-client-sg')

    sg_graph_db = aws_ec2.SecurityGroup(self, "NeptuneSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for neptune client',
      security_group_name='neptune-server-sg'
    )
    cdk.Tags.of(sg_graph_db).add('Name', 'neptune-server-sg')

    sg_graph_db.add_ingress_rule(peer=sg_graph_db, connection=aws_ec2.Port.tcp(8182), description='neptune-server-sg')
    sg_graph_db.add_ingress_rule(peer=sg_graph_db_client, connection=aws_ec2.Port.tcp(8182), description='neptune-client-sg')

    private_subnets = vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)
    availability_zones = private_subnets.availability_zones[:2]

    graph_db_subnet_group = aws_neptune.CfnDBSubnetGroup(self, 'NeptuneSubnetGroup',
      db_subnet_group_description='subnet group for neptune',
      subnet_ids=private_subnets.subnet_ids[:2],
      db_subnet_group_name=f'neptune-subnet-{self.stack_name}'
    )

    graph_db = aws_neptune.CfnDBCluster(self, 'NeptuneCluster',
      availability_zones=availability_zones,
      db_subnet_group_name=graph_db_subnet_group.db_subnet_group_name,
      db_cluster_identifier='neptune-demo',
      backup_retention_period=1,
      preferred_backup_window='08:45-09:15',
      preferred_maintenance_window='sun:18:00-sun:18:30',
      vpc_security_group_ids=[sg_graph_db.security_group_id]
    )
    graph_db.add_dependency(graph_db_subnet_group)

    graph_db_instance = aws_neptune.CfnDBInstance(self, 'NeptuneInstance',
      db_instance_class='db.r5.large',
      allow_major_version_upgrade=False,
      auto_minor_version_upgrade=False,
      availability_zone=availability_zones[0],
      db_cluster_identifier=graph_db.db_cluster_identifier,
      db_instance_identifier='neptune-demo',
      preferred_maintenance_window='sun:18:00-sun:18:30'
    )
    graph_db_instance.add_dependency(graph_db)

    graph_db_replica_instance = aws_neptune.CfnDBInstance(self, 'NeptuneReplicaInstance',
      db_instance_class='db.r5.large',
      allow_major_version_upgrade=False,
      auto_minor_version_upgrade=False,
      availability_zone=availability_zones[-1],
      db_cluster_identifier=graph_db.db_cluster_identifier,
      db_instance_identifier='neptune-demo-replica',
      preferred_maintenance_window='sun:18:00-sun:18:30'
    )
    graph_db_replica_instance.add_dependency(graph_db)
    graph_db_replica_instance.add_dependency(graph_db_instance)

    self.graph_db = graph_db
    self.sg_graph_db_client = sg_graph_db_client
    self.graph_db_subnet_group = graph_db_subnet_group

    cdk.CfnOutput(self, 'ClusterEndpoint',
      value=self.graph_db.attr_endpoint,
      export_name=f'{self.stack_name}-Endpoint')
    cdk.CfnOutput(self, 'ClusterReadEndpoint',
      value=self.graph_db.attr_read_endpoint,
      export_name=f'{self.stack_name}-ReadEndpoint')
    cdk.CfnOutput(self, 'ClusterPort',
      value=self.graph_db.attr_port,
      export_name=f'{self.stack_name}-Port')
    cdk.CfnOutput(self, 'ClusterClientSecurityGroupId',
      value=self.sg_graph_db_client.security_group_id,
      export_name=f'{self.stack_name}-ClientSecurityGroupId')
