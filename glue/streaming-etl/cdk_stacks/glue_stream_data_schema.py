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
    database_name = glue_job_input_arguments["--glue_database"] # "ventilatordb"
    table_name = glue_job_input_arguments["--glue_table_name"] # "ventilators_table",

    cfn_database = aws_glue.CfnDatabase(self, "GlueCfnDatabase",
      catalog_id=cdk.Aws.ACCOUNT_ID,
      database_input=aws_glue.CfnDatabase.DatabaseInputProperty(
        # create_table_default_permissions=[aws_glue.CfnDatabase.PrincipalPrivilegesProperty(
        #   permissions=["ALL"],
        #   principal=aws_glue.CfnDatabase.DataLakePrincipalProperty(
        #     # data_lake_principal_identifier=glue_job_role.role_arn
        #     data_lake_principal_identifier="IAM_ALLOWED_PRINCIPALS"
        #   )
        # )],
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
              name="ventilatorid",
              type="int"
            ),
            aws_glue.CfnTable.ColumnProperty(
              name="eventtime",
              type="string"
            ),
            aws_glue.CfnTable.ColumnProperty(
              name="serialnumber",
              type="string"
            ),
            aws_glue.CfnTable.ColumnProperty(
              name="pressurecontrol",
              type="int"
            ),
            aws_glue.CfnTable.ColumnProperty(
              name="o2stats",
              type="int"
            ),
            aws_glue.CfnTable.ColumnProperty(
              name="minutevolume",
              type="int"
            ),
            aws_glue.CfnTable.ColumnProperty(
              name="manufacturer",
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
