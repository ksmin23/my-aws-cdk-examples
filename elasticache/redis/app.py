#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

from aws_cdk import (
  core,
  aws_ec2,
  aws_elasticache
)


class RedisStack(core.Stack):

  def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    vpc = aws_ec2.Vpc(self, 'RedisVPC',
      max_azs=2
    )

    sg_use_elasticache = aws_ec2.SecurityGroup(self, 'RedisClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redis client',
      security_group_name='use-default-redis'
    )
    core.Tags.of(sg_use_elasticache).add('Name', 'use-default-redis')

    sg_elasticache = aws_ec2.SecurityGroup(self, 'RedisServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redis',
      security_group_name='default-redis-server'
    )
    core.Tags.of(sg_elasticache).add('Name', 'redis-server')

    sg_elasticache.add_ingress_rule(peer=sg_use_elasticache, connection=aws_ec2.Port.tcp(6379),
      description='use-default-redis')
    sg_elasticache.add_ingress_rule(peer=sg_elasticache, connection=aws_ec2.Port.all_tcp(),
      description='default-redis-server')

    elasticache_subnet_group = aws_elasticache.CfnSubnetGroup(self, 'RedisSubnetGroup',
      description='subnet group for redis',
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE).subnet_ids,
      cache_subnet_group_name='default-redis'
    )

    redis_param_group = aws_elasticache.CfnParameterGroup(self, 'RedisParamGroup',
      cache_parameter_group_family='redis5.0',
      description='parameter group for redis5.0',
      properties={
        'databases': '256', # database: 16 (default)
        'tcp-keepalive': '0', #tcp-keepalive: 300 (default)
        'maxmemory-policy': 'volatile-ttl' #maxmemory-policy: volatile-lru (default)
      }
    )

    redis_primary_only = aws_elasticache.CfnCacheCluster(self, 'RedisCache',
      cache_node_type='cache.t3.small',
      #XXX: NumCacheNodes should be 1 if engine is redis
      num_cache_nodes=1,
      engine='redis',
      engine_version='5.0.5',
      auto_minor_version_upgrade=False,
      cluster_name='elasticache-redis',
      snapshot_retention_limit=3,
      snapshot_window='17:00-19:00',
      preferred_maintenance_window='mon:19:00-mon:20:30',
      #XXX: Elasticache.CfnParameterGroup cannot be initialized with a parameter_group_name
      # https://github.com/aws-cloudformation/aws-cloudformation-coverage-roadmap/issues/484
      # https://github.com/aws/aws-cdk/issues/8180
      cache_parameter_group_name=redis_param_group.ref,
      cache_subnet_group_name=elasticache_subnet_group.cache_subnet_group_name,
      vpc_security_group_ids=[sg_elasticache.security_group_id],
      tags=[core.CfnTag(key='Name', value='redis-primary-only'),
        core.CfnTag(key='desc', value='primary only redis')]
    )
    #XXX: Subnet group must exist before ElastiCache is created 
    redis_primary_only.add_depends_on(elasticache_subnet_group)
 
    redis_with_replicas = aws_elasticache.CfnReplicationGroup(self, 'RedisCacheWithReplicas',
      cache_node_type='cache.t3.small',
      engine='redis',
      engine_version='5.0.5',
      snapshot_retention_limit=3,
      snapshot_window='19:00-21:00',
      preferred_maintenance_window='mon:21:00-mon:22:30',
      automatic_failover_enabled=True,
      auto_minor_version_upgrade=False,
      multi_az_enabled=True,
      replication_group_description='redis with replicas',
      replicas_per_node_group=1,
      cache_parameter_group_name=redis_param_group.ref,
      cache_subnet_group_name=elasticache_subnet_group.cache_subnet_group_name,
      security_group_ids=[sg_elasticache.security_group_id],
      tags=[core.CfnTag(key='Name', value='redis-with-replicas'),
        core.CfnTag(key='desc', value='primary-replica redis')]
    )
    redis_with_replicas.add_depends_on(elasticache_subnet_group)

    redis_cluster_param_group = aws_elasticache.CfnParameterGroup(self, 'RedisClusterParamGroup',
      cache_parameter_group_family='redis5.0',
      description='parameter group for redis5.0 cluster',
      properties={
        'cluster-enabled': 'yes', # Enable cluster mode
        'tcp-keepalive': '0', #tcp-keepalive: 300 (default)
        'maxmemory-policy': 'volatile-ttl' #maxmemory-policy: volatile-lru (default)
      }
    )

    redis_cluster = aws_elasticache.CfnReplicationGroup(self, 'RedisCluster',
      cache_node_type='cache.t3.small',
      engine='redis',
      engine_version='5.0.5',
      snapshot_retention_limit=3,
      snapshot_window='19:00-21:00',
      preferred_maintenance_window='mon:21:00-mon:22:30',
      automatic_failover_enabled=True,
      auto_minor_version_upgrade=False,
      #XXX: Each Node Group needs to have at least one replica for Multi-AZ enabled Replication Group
      multi_az_enabled=False,
      replication_group_description='redis5.0 cluster on',
      num_node_groups=3,
      cache_parameter_group_name=redis_cluster_param_group.ref,
      cache_subnet_group_name=elasticache_subnet_group.cache_subnet_group_name,
      security_group_ids=[sg_elasticache.security_group_id],
      tags=[core.CfnTag(key='Name', value='redis-cluster'),
        core.CfnTag(key='desc', value='primary-replica redis')]
    )
    redis_cluster.add_depends_on(elasticache_subnet_group)


app = core.App()
RedisStack(app, "redis")

app.synth()
