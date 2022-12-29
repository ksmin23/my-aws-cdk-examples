#!/usr/bin/env python3
import os

from cdk_stacks import (
  VpcStack,
  OpsAdminIAMUserStack,
  OpsServerlessInVPCStack,
  OpsClientEC2InstanceStack,
)

import aws_cdk as cdk


AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

vpc_stack = VpcStack(app, "OpenSearchServerlessVpc",
  env=AWS_ENV)

ops_admin_user = OpsAdminIAMUserStack(app, "OpsAdminIAMUser")

ops_serverless_in_vpc_stack = OpsServerlessInVPCStack(app, "OpenSearchServerlessInVpcStack",
  ops_admin_user.user_arn,
  vpc_stack.vpc,
  env=AWS_ENV)
ops_serverless_in_vpc_stack.add_dependency(ops_admin_user)
ops_serverless_in_vpc_stack.add_dependency(vpc_stack)

ops_client_instance = OpsClientEC2InstanceStack(app, "OpenSearchCleintInstance",
  vpc_stack.vpc,
  ops_serverless_in_vpc_stack.opensearch_client_sg,
  env=AWS_ENV)
ops_client_instance.add_dependency(ops_serverless_in_vpc_stack)

app.synth()
