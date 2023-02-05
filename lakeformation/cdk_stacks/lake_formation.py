#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_lakeformation
)
from constructs import Construct

class DataLakePermissionsStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, job_role, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    database_name = self.node.try_get_context('database_name')

    #XXXX: The role assumed by cdk is not a data lake administrator.
    # So, deploying PrincipalPermissions meets the error such as:
    # "Resource does not exist or requester is not authorized to access requested permissions."
    # In order to solve the error, it is necessary to promote the cdk execution role to the data lake administrator.
    # For example, https://github.com/aws-samples/data-lake-as-code/blob/mainline/lib/stacks/datalake-stack.ts#L68
    cfn_data_lake_settings = aws_lakeformation.CfnDataLakeSettings(self, "CfnDataLakeSettings",
      admins=[aws_lakeformation.CfnDataLakeSettings.DataLakePrincipalProperty(
        data_lake_principal_identifier=cdk.Fn.sub(self.synthesizer.cloud_formation_execution_role_arn)
      )]
    )

    lf_permissions_on_database = aws_lakeformation.CfnPrincipalPermissions(self, "CfnPrincipalPermissions",
      permissions=["CREATE_TABLE", "DROP", "ALTER", "DESCRIBE"],
      permissions_with_grant_option=[],
      principal=aws_lakeformation.CfnPrincipalPermissions.DataLakePrincipalProperty(
        data_lake_principal_identifier=job_role.role_arn
      ),
      resource=aws_lakeformation.CfnPrincipalPermissions.ResourceProperty(
        database=aws_lakeformation.CfnPrincipalPermissions.DatabaseResourceProperty(
          catalog_id=cdk.Aws.ACCOUNT_ID,
          name=database_name
        )
      )
    )
    lf_permissions_on_database.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    #XXX: In order to keep resource destruction order,
    # set dependency between CfnDataLakeSettings and CfnPrincipalPermissions
    lf_permissions_on_database.add_dependency(cfn_data_lake_settings)

    lf_permissions_on_table = aws_lakeformation.CfnPrincipalPermissions(self, "CfnPrincipalPermissions2",
      permissions=["SELECT", "INSERT", "DELETE", "DESCRIBE", "ALTER"],
      permissions_with_grant_option=[],
      principal=aws_lakeformation.CfnPrincipalPermissions.DataLakePrincipalProperty(
        data_lake_principal_identifier=job_role.role_arn
      ),
      resource=aws_lakeformation.CfnPrincipalPermissions.ResourceProperty(
        #XXX: Can't specify a TableWithColumns resource and a Table resource
        table=aws_lakeformation.CfnPrincipalPermissions.TableResourceProperty(
          catalog_id=cdk.Aws.ACCOUNT_ID,
          database_name=database_name,
          # name="ALL_TABLES",
          table_wildcard={}
        )
      )
    )
    lf_permissions_on_table.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
    lf_permissions_on_table.add_dependency(cfn_data_lake_settings)

    cdk.CfnOutput(self, f'{self.stack_name}_Principal',
      value=lf_permissions_on_database.attr_principal_identifier)
