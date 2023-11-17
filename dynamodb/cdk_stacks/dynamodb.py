#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_dynamodb
)
from constructs import Construct

class DynamodbStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    ddb_table = aws_dynamodb.Table(self, "SimpleDynamoDbTable",
      table_name="SimpleTable",
      # removal_policy=cdk.RemovalPolicy.DESTROY,
      partition_key=aws_dynamodb.Attribute(name="pkid",
        type=aws_dynamodb.AttributeType.STRING),
      sort_key=aws_dynamodb.Attribute(name="sortkey",
        type=aws_dynamodb.AttributeType.NUMBER),
      time_to_live_attribute="ttl",
      billing_mode=aws_dynamodb.BillingMode.PROVISIONED,
      read_capacity=15,
      write_capacity=5,
    )

    cdk.CfnOutput(self, 'DynamoDBTableName', value=ddb_table.table_name,
      export_name=f'{self.stack_name}-TableName')
