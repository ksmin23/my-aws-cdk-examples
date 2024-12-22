#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_memorydb
)
from constructs import Construct


class MemoryDBStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, memorydb_acl, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    memorydb_cluster_props = self.node.try_get_context('memorydb')
    memorydb_cluster_name = memorydb_cluster_props['cluster_name']

    sg_memorydb_client = aws_ec2.SecurityGroup(self, 'MemoryDBClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for memorydb client',
      security_group_name=f'memorydb-client-sg-{memorydb_cluster_name.lower()}'
    )
    cdk.Tags.of(sg_memorydb_client).add('Name', 'memorydb-client-sg')

    sg_memorydb_server = aws_ec2.SecurityGroup(self, 'MemoryDBServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redis',
      security_group_name=f'memorydb-server-sg-{memorydb_cluster_name.lower()}'
    )
    cdk.Tags.of(sg_memorydb_server).add('Name', 'memorydb-server-sg')

    sg_memorydb_server.add_ingress_rule(peer=sg_memorydb_client, connection=aws_ec2.Port.tcp(6379),
      description='memorydb-client-sg')
    sg_memorydb_server.add_ingress_rule(peer=sg_memorydb_server, connection=aws_ec2.Port.all_tcp(),
      description='memorydb-server-sg')

    memorydb_subnet_group = aws_memorydb.CfnSubnetGroup(self, 'MemoryDBSubnetGroup',
      description='subnet group for memorydb',
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
      subnet_group_name=f'memory-db-subnet-for-{memorydb_cluster_name.lower()}',
    )
    memorydb_subnet_group.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY,
      apply_to_update_replace_policy=False)

    multi_region_cluster_name = self.node.try_get_context('memorydb_multi_region_cluster_name')
    cluster_name = f"{memorydb_cluster_name}-{cdk.Aws.REGION}" if multi_region_cluster_name else memorydb_cluster_name

    memorydb_cluster = aws_memorydb.CfnCluster(self, 'MemoryDBCluster',
      # Only active or modifying ACL can be associated to a cluster.
      acl_name=memorydb_acl.acl_name,
      cluster_name=cluster_name,
      node_type=memorydb_cluster_props.get("node_type", "db.r7g.xlarge"),
      auto_minor_version_upgrade=False,
      cluster_endpoint=aws_memorydb.CfnCluster.EndpointProperty(
        port=6379
      ),
      engine=memorydb_cluster_props.get("engine", "Redis"),
      engine_version=memorydb_cluster_props.get("engine_version", "7.1"),
      maintenance_window='mon:21:00-mon:22:30',
      multi_region_cluster_name=multi_region_cluster_name,
      #XXX: total number of nodes = num_shards * (num_replicas_per_shard + 1)
      num_replicas_per_shard=memorydb_cluster_props.get("num_replicas_per_shard", 1),
      num_shards=memorydb_cluster_props.get("num_shards", 1),
      security_group_ids=[sg_memorydb_server.security_group_id],
      snapshot_retention_limit=3,
      snapshot_window='16:00-20:00',
      subnet_group_name=memorydb_subnet_group.subnet_group_name,
      tags=[
        cdk.CfnTag(key='Name', value='memorydb-cluster-for-redis'),
        cdk.CfnTag(key='desc', value='memorydb cluster for redis')
      ],
      tls_enabled=True
    )
    memorydb_cluster.add_dependency(memorydb_subnet_group)

    memorydb_cluster.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY,
      apply_to_update_replace_policy=False)


    cdk.CfnOutput(self, 'MemoryDBClusterName',
      value=memorydb_cluster.cluster_name,
      export_name=f'{self.stack_name}-MemoryDBClusterName')
    cdk.CfnOutput(self, 'MemoryDBClusterEndpoint',
      value=memorydb_cluster.attr_cluster_endpoint_address,
      export_name=f'{self.stack_name}-MemoryDBClusterEndpoint')
    cdk.CfnOutput(self, 'MemoryDBEngine',
      value=memorydb_cluster.engine,
      export_name=f'{self.stack_name}-MemoryDBEngine')
    cdk.CfnOutput(self, 'MemoryDBEngineVersion',
      value=memorydb_cluster.engine_version,
      export_name=f'{self.stack_name}-MemoryDBEngineVersion')
    cdk.CfnOutput(self, 'MemoryDBClientSecurityGroupId',
      value=sg_memorydb_client.security_group_id,
      export_name=f'{self.stack_name}-MemoryDBClientSecurityGroupId')
