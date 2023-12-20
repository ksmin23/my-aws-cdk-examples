#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

from cdk_stacks import (
  VpcStack,
  OpsAdminIAMUserStack,
  OpssVpcEndpointStack,
  OpsServerlessInVPCStack,
  OpsClientEC2InstanceStack,
  OpenSearchSecurityGroupStack
)

import aws_cdk as cdk


AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

vpc_stack = VpcStack(app, "OpenSearchServerlessVpc",
  env=AWS_ENV)

ops_admin_user = OpsAdminIAMUserStack(app, "OpsAdminIAMUser")

ops_security_groups = OpenSearchSecurityGroupStack(app, "OpenSearchSecurityGroups",
  vpc_stack.vpc,
  env=AWS_ENV)
ops_security_groups.add_dependency(vpc_stack)

ops_security_groups.add_dependency(vpc_stack)
vpc_endpoint_stack = OpssVpcEndpointStack(app, "OpenSearchServerlessVpcEndpoint",
  vpc_stack.vpc,
  ops_security_groups.opensearch_cluster_sg,
  env=AWS_ENV
)
vpc_endpoint_stack.add_dependency(ops_security_groups)

ops_serverless_in_vpc_stack = OpsServerlessInVPCStack(app, "OpenSearchServerlessInVpcStack",
  ops_admin_user.user_arn,
  vpc_endpoint_stack.vpc_endpoint_id,
  env=AWS_ENV)
ops_serverless_in_vpc_stack.add_dependency(ops_admin_user)
ops_serverless_in_vpc_stack.add_dependency(vpc_endpoint_stack)

ops_client_instance = OpsClientEC2InstanceStack(app, "OpenSearchCleintInstance",
  vpc_stack.vpc,
  ops_security_groups.opensearch_client_sg,
  env=AWS_ENV)
ops_client_instance.add_dependency(ops_serverless_in_vpc_stack)

app.synth()
