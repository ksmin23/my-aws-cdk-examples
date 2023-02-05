#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_glue
)
from constructs import Construct


class GlueCatalogDatabaseStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    database_name = self.node.try_get_context('database_name')

    cfn_database = aws_glue.CfnDatabase(self, f"GlueCfnDatabase",
      catalog_id=cdk.Aws.ACCOUNT_ID,
      database_input=aws_glue.CfnDatabase.DatabaseInputProperty(
        name=database_name
      )
    )
    cfn_database.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, f'{self.stack_name}_GlueDatabaseName',
      value=cfn_database.database_input.name)
