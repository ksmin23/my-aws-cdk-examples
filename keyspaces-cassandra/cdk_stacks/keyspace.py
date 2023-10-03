import aws_cdk as cdk

from aws_cdk import (
  # Duration,
  Stack,
  aws_cassandra,
)
from constructs import Construct

class KeyspaceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    KEYSPACE_CONFIG = self.node.try_get_context('keyspace_config')
    keyspace_name = KEYSPACE_CONFIG['keyspace_name']
    replication_specification = KEYSPACE_CONFIG['replication_specification']

    cfn_keyspace = aws_cassandra.CfnKeyspace(self, "CfnKeyspace",
      keyspace_name=keyspace_name,
      replication_specification=replication_specification
    )
    cfn_keyspace.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, 'KeyspaceName', value=cfn_keyspace.keyspace_name,
      export_name=f'{self.stack_name}-KeyspaceName')