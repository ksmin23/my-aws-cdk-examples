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


class RedisStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sg_use_elasticache = aws_ec2.SecurityGroup(self, 'RedisClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redis client',
      security_group_name=f'{self.stack_name}-redis-client-sg'
    )
    cdk.Tags.of(sg_use_elasticache).add('Name', 'redis-client-sg')

    sg_elasticache = aws_ec2.SecurityGroup(self, 'RedisServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redis',
      security_group_name=f'{self.stack_name}-redis-server-sg'
    )
    cdk.Tags.of(sg_elasticache).add('Name', 'redis-server-sg')

    sg_elasticache.add_ingress_rule(peer=sg_use_elasticache, connection=aws_ec2.Port.tcp(6379),
      description='redis-client-sg')
    sg_elasticache.add_ingress_rule(peer=sg_elasticache, connection=aws_ec2.Port.all_tcp(),
      description='redis-server-sg')

    elasticache_subnet_group = aws_elasticache.CfnSubnetGroup(self, 'RedisSubnetGroup',
      description='subnet group for redis',
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
      cache_subnet_group_name=f'{self.stack_name}-redis-subnet'
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

    redis_primary_only = aws_elasticache.CfnCacheCluster(self, 'RedisCache',
      cache_node_type='cache.t3.small',
      #XXX: NumCacheNodes should be 1 if engine is redis
      num_cache_nodes=1,
      engine='redis',

      #XXX: Supported ElastiCache for Redis versions
      # https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/supported-engine-versions.html
      engine_version='7.0',
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
      tags=[cdk.CfnTag(key='Name', value='redis-primary-only'),
        cdk.CfnTag(key='desc', value='primary only redis')]
    )
    #XXX: Subnet group must exist before ElastiCache is created
    redis_primary_only.add_dependency(elasticache_subnet_group)
    redis_primary_only.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, 'RedisEndpoint', value=redis_primary_only.attr_redis_endpoint_address,
                  export_name=f'{self.stack_name}-RedisEndpoint')
    cdk.CfnOutput(self, 'RedisPort', value=redis_primary_only.attr_redis_endpoint_port,
                  export_name=f'{self.stack_name}-RedisPort')
