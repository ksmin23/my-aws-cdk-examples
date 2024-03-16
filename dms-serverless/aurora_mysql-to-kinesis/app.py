#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

from cdk_stacks import (
  VpcStack,
  DmsIAMRolesStack,
  DMSServerlessAuroraMysqlToKinesisStack
)

import aws_cdk as cdk


AWS_ENV = cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')
)

app = cdk.App()

vpc_stack = VpcStack(app, "DMSAuroraMysqlToKDSVPCStack",
  env=AWS_ENV
)

dms_iam_permissions = DmsIAMRolesStack(app, "DMSRequiredIAMRolesStack")
dms_iam_permissions.add_dependency(vpc_stack)

dms_task_stack = DMSServerlessAuroraMysqlToKinesisStack(app, "DMSServerlessAuroraMysqlToKDSStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
dms_task_stack.add_dependency(dms_iam_permissions)

app.synth()
