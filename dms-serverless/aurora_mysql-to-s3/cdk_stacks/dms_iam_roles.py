#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam
)
from constructs import Construct


class DmsIAMRolesStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    dms_vpc_role = aws_iam.Role(self, 'DMSVpcRole',
      role_name='dms-vpc-role',
      assumed_by=aws_iam.ServicePrincipal('dms.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonDMSVPCManagementRole'),
      ]
    )

    dms_cloudwatch_logs_role = aws_iam.Role(self, 'DMSCloudWatchLogsRole',
      role_name='dms-cloudwatch-logs-role',
      assumed_by=aws_iam.ServicePrincipal('dms.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonDMSCloudWatchLogsRole'),
      ]
    )


    cdk.CfnOutput(self, 'DMSVpcRoleArn',
      value=dms_vpc_role.role_arn,
      export_name=f'{self.stack_name}-DMSVpcRoleArn')
    cdk.CfnOutput(self, 'DMSCloudWatchLogsRoleArn',
      value=dms_cloudwatch_logs_role.role_arn,
      export_name=f'{self.stack_name}-DMSCloudWatchLogsRoleArn')
