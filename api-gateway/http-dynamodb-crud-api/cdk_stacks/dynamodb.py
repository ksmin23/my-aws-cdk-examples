#!/usr/bin/env python3
import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_dynamodb,
)
from constructs import Construct


class DynamoDBStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    dynamodb_config = self.node.try_get_context("dynamodb")
    DDB_TABLE_NAME = dynamodb_config['table_name']
    PARTITION_KEY = dynamodb_config['partition_key']
    TIME_TO_LIVE_ATTRIBUTE = dynamodb_config['time_to_live_attribute']

    ddb_table = aws_dynamodb.Table(self, f"{self.stack_name}_DynamoDbTable",
      table_name=DDB_TABLE_NAME,
      removal_policy=cdk.RemovalPolicy.DESTROY,
      partition_key=aws_dynamodb.Attribute(name=PARTITION_KEY,
        type=aws_dynamodb.AttributeType.STRING),
      time_to_live_attribute=TIME_TO_LIVE_ATTRIBUTE,
      billing_mode=aws_dynamodb.BillingMode.PROVISIONED,
      read_capacity=15,
      write_capacity=5,
    )

    self.dynamodb_table = ddb_table

    cdk.CfnOutput(self, f'{self.stack_name}_TableName',
      value=self.dynamodb_table.table_name,
      export_name='DynamoDBTableName')