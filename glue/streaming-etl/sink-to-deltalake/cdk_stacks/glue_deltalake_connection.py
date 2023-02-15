import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_glue,
)
from constructs import Construct

class DeltalakeConnectionStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    glue_deltalake_connection_name = self.node.try_get_context('glue_connections_name')

    connection_properties = {
      "CONNECTOR_TYPE": "Spark",
      "CONNECTOR_URL": "https://709825985650.dkr.ecr.us-east-1.amazonaws.com/amazon-web-services/glue/delta:1.0.0-glue3.0-2",
      "CONNECTOR_CLASS_NAME": "org.apache.spark.sql.delta.sources.DeltaDataSource"
    }

    cfn_connection = aws_glue.CfnConnection(self, "GlueDeltaLakeConnection",
      catalog_id=cdk.Aws.ACCOUNT_ID,
      connection_input=aws_glue.CfnConnection.ConnectionInputProperty(
        connection_type="MARKETPLACE",

        connection_properties=connection_properties,
        description="Delta Lake Connector 1.0.0 for AWS Glue 3.0",
        name=glue_deltalake_connection_name
      )
    )

    cfn_connection.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

