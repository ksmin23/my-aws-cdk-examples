import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_glue
)
from constructs import Construct


class GlueCatalogDatabaseStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    glue_kinesis_table = self.node.try_get_context('glue_job_input_arguments')
    database_name = glue_kinesis_table['--database_name']

    cfn_database = aws_glue.CfnDatabase(self, "GlueCfnDatabase",
      catalog_id=cdk.Aws.ACCOUNT_ID,
      database_input=aws_glue.CfnDatabase.DatabaseInputProperty(
        name=database_name
      )
    )
    cfn_database.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, f'{self.stack_name}_GlueDatabaseName',
      value=cfn_database.database_input.name)
