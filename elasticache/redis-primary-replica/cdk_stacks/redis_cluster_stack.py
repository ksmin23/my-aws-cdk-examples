#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_elasticache
)
from constructs import Construct


class RedisClusterStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sg_use_elasticache = aws_ec2.SecurityGroup(self, 'RedisClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redis client',
      security_group_name='redis-client-sg'
    )
    cdk.Tags.of(sg_use_elasticache).add('Name', 'redis-client-sg')

    sg_elasticache = aws_ec2.SecurityGroup(self, 'RedisServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redis server',
      security_group_name='redis-server-sg'
    )
    cdk.Tags.of(sg_elasticache).add('Name', 'redis-server-sg')

    sg_elasticache.add_ingress_rule(peer=sg_use_elasticache, connection=aws_ec2.Port.tcp(6379),
      description='redis-client-sg')
    sg_elasticache.add_ingress_rule(peer=sg_elasticache, connection=aws_ec2.Port.all_tcp(),
      description='redis-server-sg')

    redis_cluster_subnet_group = aws_elasticache.CfnSubnetGroup(self, 'RedisSubnetGroup',
      description='subnet group for redis',
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
      cache_subnet_group_name=f'{self.stack_name}-redis-cluster'
    )

    redis_param_group = aws_elasticache.CfnParameterGroup(self, 'RedisParamGroup',
      cache_parameter_group_family='redis7',
      description='parameter group for redis7.0',
      properties={
        'databases': '256', # database: 16 (default)
        'tcp-keepalive': '0', #tcp-keepalive: 300 (default)
        'maxmemory-policy': 'volatile-ttl' #maxmemory-policy: volatile-lru (default)
      }
    )
    redis_param_group.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    redis_with_replicas = aws_elasticache.CfnReplicationGroup(self, 'RedisCacheWithReplicas',
      replication_group_description='redis with replicas',
      # cache_node_type='cache.t3.small',
      cache_node_type='cache.r6g.large',
      engine='redis',

      #XXX: Supported ElastiCache for Redis versions
      # https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/supported-engine-versions.html
      engine_version='7.0',

      #XXX: Auto-failover must be enabled on the cluster with a minimum of 1 replica.
      # https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/modify-cluster-mode.html
      replicas_per_node_group=1,
      automatic_failover_enabled=True,

      #XXX: Each Node Group needs to have at least one replica for Multi-AZ enabled Replication Group
      multi_az_enabled=True,
      cache_parameter_group_name=redis_param_group.ref,
      cache_subnet_group_name=redis_cluster_subnet_group.cache_subnet_group_name,
      security_group_ids=[sg_elasticache.security_group_id],
      snapshot_retention_limit=3,
      snapshot_window='19:00-21:00',
      preferred_maintenance_window='mon:21:00-mon:22:30',
      auto_minor_version_upgrade=False,
      tags=[cdk.CfnTag(key='Name', value='redis-with-replicas'),
        cdk.CfnTag(key='desc', value='primary-replica redis')]
    )
    redis_with_replicas.add_dependency(redis_cluster_subnet_group)
    redis_with_replicas.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, 'RedisPrimaryEndpoint', value=redis_with_replicas.attr_primary_end_point_address,
                  export_name=f'{self.stack_name}-RedisPrimaryEndpoint')
    cdk.CfnOutput(self, 'RedisPrimaryPort', value=redis_with_replicas.attr_primary_end_point_port,
                  export_name=f'{self.stack_name}-RedisPrimaryPort')
    cdk.CfnOutput(self, 'RedisReplicaEndpoints', value=redis_with_replicas.attr_read_end_point_addresses,
                  export_name=f'{self.stack_name}-RedisReplicaEndpoints')
    cdk.CfnOutput(self, 'RedisReplicaPorts', value=redis_with_replicas.attr_read_end_point_ports,
                  export_name=f'{self.stack_name}-RedisReplicaPorts')
