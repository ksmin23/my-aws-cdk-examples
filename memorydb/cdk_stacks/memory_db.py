#!/usr/bin/env python3
import os

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

    sg_use_memorydb = aws_ec2.SecurityGroup(self, 'MemoryDBClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for memorydb client',
      security_group_name='use-default-memorydb'
    )
    cdk.Tags.of(sg_use_memorydb).add('Name', 'use-default-memorydb')

    sg_memorydb = aws_ec2.SecurityGroup(self, 'MemoryDBServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redis',
      security_group_name='default-memorydb-server'
    )
    cdk.Tags.of(sg_memorydb).add('Name', 'memorydb-server')

    sg_memorydb.add_ingress_rule(peer=sg_use_memorydb, connection=aws_ec2.Port.tcp(6379),
      description='use-default-memorydb')
    sg_memorydb.add_ingress_rule(peer=sg_memorydb, connection=aws_ec2.Port.all_tcp(),
      description='default-memorydb-server')

    memorydb_subnet_group = aws_memorydb.CfnSubnetGroup(self, 'MemoryDBSubnetGroup',
      description='subnet group for memorydb',
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
      subnet_group_name='default-memorydb'
    )

    memorydb_cluster = aws_memorydb.CfnCluster(self, 'MemoryDBCluster',
      cluster_name='my-memorydb-cluster',
      # Only active or modifying ACL can be associated to a cluster.
      acl_name=memorydb_acl.acl_name,
      auto_minor_version_upgrade=False,
      engine_version='6.2',
      maintenance_window='mon:21:00-mon:22:30',
      node_type='db.r6g.large',
      #XXX: total number of nodes = num_shards * (num_replicas_per_shard + 1)
      num_replicas_per_shard=1,
      num_shards=3,
      security_group_ids=[sg_memorydb.security_group_id],
      snapshot_retention_limit=3,
      snapshot_window='16:00-20:00',
      tags=[cdk.CfnTag(key='Name', value='memorydb-cluster'),
        cdk.CfnTag(key='desc', value='memorydb cluster')],
      tls_enabled=True
    )

    memorydb_cluster.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY,
      apply_to_update_replace_policy=False)

    cdk.CfnOutput(self, 'MemoryDBClusterName', value=memorydb_cluster.cluster_name,
      export_name=f'{self.stack_name}-MemoryDBClusterName')
    cdk.CfnOutput(self, 'MemoryDBClusterEndpoint', value=memorydb_cluster.attr_cluster_endpoint_address,
      export_name=f'{self.stack_name}-MemoryDBClusterEndpoint')
    cdk.CfnOutput(self, 'MemoryDBEngineVersion', value=memorydb_cluster.engine_version,
      export_name=f'{self.stack_name}-MemoryDBEngineVersion')
