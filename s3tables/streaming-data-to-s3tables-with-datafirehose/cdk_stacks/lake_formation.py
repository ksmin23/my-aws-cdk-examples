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

  def __init__(self,
               scope: Construct,
               construct_id: str,
               s3table_bucket_name,
               firehose_role,
               resource_link,
               **kwargs) -> None:

    super().__init__(scope, construct_id, **kwargs)

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

    lf_permissions_resource_link = aws_lakeformation.CfnPermissions(self, "GrantPermissionsToResourceLink",
      data_lake_principal=aws_lakeformation.CfnPermissions.DataLakePrincipalProperty(
        data_lake_principal_identifier=firehose_role.role_arn
      ),
      resource=aws_lakeformation.CfnPermissions.ResourceProperty(
        database_resource=aws_lakeformation.CfnPermissions.DatabaseResourceProperty(
          catalog_id=cdk.Aws.ACCOUNT_ID,
          name=resource_link.ref
        )
      ),
      permissions=["DESCRIBE"]
    )
    lf_permissions_resource_link.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    #XXX: In order to keep resource destruction order,
    # set dependency between CfnDataLakeSettings and CfnPrincipalPermissions
    lf_permissions_resource_link.add_dependency(cfn_data_lake_settings)


    s3tables_config = self.node.try_get_context("s3_tables")
    database_name = s3tables_config['namespace_name']
    table_name = s3tables_config['table_name']
    s3tables_catalog_id = f"{self.account}:s3tablescatalog/{s3table_bucket_name}"

    # Grant to Catalog / tablebucket / namespace / table
    lf_permissions_table = aws_lakeformation.CfnPermissions(self, "GrantPermissionsToTable",
      data_lake_principal=aws_lakeformation.CfnPermissions.DataLakePrincipalProperty(
        data_lake_principal_identifier=firehose_role.role_arn
      ),
      resource=aws_lakeformation.CfnPermissions.ResourceProperty(
        table_resource=aws_lakeformation.CfnPermissions.TableResourceProperty(
          catalog_id=s3tables_catalog_id,
          database_name=database_name,
          name=table_name,
        )
      ),
      permissions=["ALL"]
    )
    lf_permissions_table.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    #XXX: In order to keep resource destruction order,
    # set dependency between CfnDataLakeSettings and CfnPrincipalPermissions
    lf_permissions_table.add_dependency(cfn_data_lake_settings)
