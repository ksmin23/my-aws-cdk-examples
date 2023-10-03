import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_cassandra,
)
from constructs import Construct

class KeyspaceTableStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    KEYSPACE_TABLES = self.node.try_get_context('keyspace_tables')
    for idx, table_props in enumerate(KEYSPACE_TABLES):
      cfn_table = aws_cassandra.CfnTable(self, f"CfnKespaceTable_{idx}_",
        keyspace_name=table_props['keyspace_name'],
        table_name=table_props['table_name'],
        partition_key_columns=[aws_cassandra.CfnTable.ColumnProperty(**column)
          for column in table_props['partition_key_columns']],
        clustering_key_columns=[aws_cassandra.CfnTable.ClusteringKeyColumnProperty(
          column=aws_cassandra.CfnTable.ColumnProperty(**elem['column']),
          order_by=elem["order_by"]
        ) for elem in table_props['clustering_key_columns']],
        regular_columns=[aws_cassandra.CfnTable.ColumnProperty(**column)
          for column in table_props['regular_columns']],
        billing_mode=table_props['billing_mode'],
        point_in_time_recovery_enabled=False,
        tags=[cdk.CfnTag(key=k, value=v) for k, v in table_props['tags'].items()]
      )

      cfn_table.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

