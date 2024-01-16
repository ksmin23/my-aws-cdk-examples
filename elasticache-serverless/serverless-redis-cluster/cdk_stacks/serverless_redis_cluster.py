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


class ServerlessRedisClusterStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sg_use_elasticache = aws_ec2.SecurityGroup(self, 'RedisClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redis client',
      security_group_name='redis-cluster-client-sg'
    )
    cdk.Tags.of(sg_use_elasticache).add('Name', 'redis-cluster-client-sg')

    sg_elasticache = aws_ec2.SecurityGroup(self, 'RedisServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redis server',
      security_group_name='redis-cluster-server-sg'
    )
    cdk.Tags.of(sg_elasticache).add('Name', 'redis-cluster-server-sg')

    sg_elasticache.add_ingress_rule(peer=sg_use_elasticache, connection=aws_ec2.Port.tcp(6379),
      description='redis-cluster-client-sg')
    sg_elasticache.add_ingress_rule(peer=sg_elasticache, connection=aws_ec2.Port.all_tcp(),
      description='redis-cluster-server-sg')

    serverless_redis = aws_elasticache.CfnServerlessCache(self, 'ServerlessRedisCache',
      engine='redis',
      serverless_cache_name='serverless-redis',

      cache_usage_limits=aws_elasticache.CfnServerlessCache.CacheUsageLimitsProperty(
        data_storage=aws_elasticache.CfnServerlessCache.DataStorageProperty(
          maximum=13,
          unit='GB'
        ),
        ecpu_per_second=aws_elasticache.CfnServerlessCache.ECPUPerSecondProperty(
          maximum=15000000
        )
      ),
      daily_snapshot_time='19:00', # HH:MM (UTC format)
      # major_engine_version='7', #XXX: Specified engine does not support major engine version (7.0)
      security_group_ids=[sg_elasticache.security_group_id],
      snapshot_retention_limit=3,
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
      # user_group_id="userGroupId" #XXX: ???
    )
    serverless_redis.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, 'RedisEndpoint',
      value=serverless_redis.attr_endpoint_address,
      export_name=f'{self.stack_name}-RedisEndpoint')
    cdk.CfnOutput(self, 'RedisClusterReaderEndpoint',
      value=serverless_redis.attr_reader_endpoint_address,
      export_name=f'{self.stack_name}-RedisClusterReaderEndpoint')
