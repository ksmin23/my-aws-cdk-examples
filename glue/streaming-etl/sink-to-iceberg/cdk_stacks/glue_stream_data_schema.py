import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_glue
)
from constructs import Construct


class GlueStreamDataSchemaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, kinesis_stream, glue_job_role, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    glue_job_input_arguments = self.node.try_get_context('glue_job_input_arguments')
    database_name = glue_job_input_arguments["--database_name"]
    table_name = glue_job_input_arguments["--kinesis_table_name"]

    cfn_database = aws_glue.CfnDatabase(self, "GlueCfnDatabase",
      catalog_id=cdk.Aws.ACCOUNT_ID,
      database_input=aws_glue.CfnDatabase.DatabaseInputProperty(
        name=database_name
      )
    )
    cfn_database.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cfn_table = aws_glue.CfnTable(self, "GlueCfnTable",
      catalog_id=cdk.Aws.ACCOUNT_ID,
      database_name=database_name,
      table_input=aws_glue.CfnTable.TableInputProperty(
        name=table_name,
        parameters={"classification": "json"},
        storage_descriptor=aws_glue.CfnTable.StorageDescriptorProperty(
          columns=[
            aws_glue.CfnTable.ColumnProperty(
              name="name",
              type="string"
            ),
            aws_glue.CfnTable.ColumnProperty(
              name="age",
              type="int"
            ),
            aws_glue.CfnTable.ColumnProperty(
              name="m_time",
              type="string"
            ),
          ],
          input_format="org.apache.hadoop.mapred.TextInputFormat",
          location=kinesis_stream.stream_name,
          output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
          parameters={
            "streamARN": kinesis_stream.stream_arn,
            "typeOfData": "kinesis"
          },
          serde_info=aws_glue.CfnTable.SerdeInfoProperty(
            serialization_library="org.openx.data.jsonserde.JsonSerDe"
          )
        ),
        table_type="EXTERNAL_TABLE"
      )
    )

    cfn_table.add_dependency(cfn_database)
    cfn_table.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, f'{self.stack_name}_GlueDatabaseName', value=cfn_table.database_name)
