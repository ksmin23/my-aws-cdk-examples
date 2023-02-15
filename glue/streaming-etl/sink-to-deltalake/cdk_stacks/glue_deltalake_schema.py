import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_glue
)
from constructs import Construct


class GlueDeltaLakeSchemaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    glue_job_input_arguments = self.node.try_get_context('glue_job_input_arguments')
    database_name = glue_job_input_arguments['--database_name']
    location_uri = os.path.dirname(glue_job_input_arguments['--delta_s3_path'])

    cfn_database = aws_glue.CfnDatabase(self, "GlueCfnDatabaseOnDeltaLake",
      catalog_id=cdk.Aws.ACCOUNT_ID,
      database_input=aws_glue.CfnDatabase.DatabaseInputProperty(
        name=database_name,
        location_uri=location_uri
      )
    )
    cfn_database.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, f'{self.stack_name}_DeltaLakeDatabaseName', value=cfn_database.database_input.name)
    cdk.CfnOutput(self, f'{self.stack_name}_DeltaLakeLocationUri', value=cfn_database.database_input.location_uri)
