#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_memorydb
)
from constructs import Construct

class MemoryDBMultiRegionClusterStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    multi_region_cluster_props = self.node.try_get_context('memorydb_mlti_region_cluster')

    cfn_multi_region_cluster = aws_memorydb.CfnMultiRegionCluster(self, "MemDBCfnMultiRegionCluster",
      node_type=multi_region_cluster_props.get("node_type", "db.r7g.xlarge"),
      engine=multi_region_cluster_props.get("engine", "Valkey"),
      engine_version=multi_region_cluster_props.get("engine_version", "7.3"),
      multi_region_cluster_name_suffix=multi_region_cluster_props.get("multi_region_cluster_name_suffix", "demo"),
      multi_region_parameter_group_name=multi_region_cluster_props.get("multi_region_parameter_group_name", None),
      num_shards=multi_region_cluster_props.get("num_shards", 1),
      tls_enabled=True,
      update_strategy="COORDINATED"
    )

    cfn_multi_region_cluster.apply_removal_policy(policy=cdk.RemovalPolicy.DESTROY)


    cdk.CfnOutput(self, 'MemDBMultiRegionClusterName',
      value=cfn_multi_region_cluster.attr_multi_region_cluster_name,
      export_name=f'{self.stack_name}-MultiRegionClusterName')
    cdk.CfnOutput(self, 'MemDBMultiRegionClusterNumShards',
      value=str(cfn_multi_region_cluster.num_shards),
      export_name=f'{self.stack_name}-MultiRegionClusterNumShards')
    cdk.CfnOutput(self, 'MemDBMultiRegionEngine',
      value=cfn_multi_region_cluster.engine,
      export_name=f'{self.stack_name}-MultiRegionEngine')
    cdk.CfnOutput(self, 'MemDBMultiRegionEngineVersion',
      value=cfn_multi_region_cluster.engine_version,
      export_name=f'{self.stack_name}-MultiRegionEngineVersion')
