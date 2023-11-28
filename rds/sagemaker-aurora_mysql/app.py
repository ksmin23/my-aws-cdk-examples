#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  AuroraMysqlStack,
  SageMakerNotebookStack
)

APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, 'SMAuroraMySQLVpcStack',
  env=APP_ENV)

aurora_mysql_stack = AuroraMysqlStack(app, 'SMAuroraMySQLStack',
  vpc_stack.vpc,
  env=APP_ENV
)
aurora_mysql_stack.add_dependency(vpc_stack)

sm_notebook_stack = SageMakerNotebookStack(app, 'SMAuroraMySQLNotebookStack',
  vpc_stack.vpc,
  aurora_mysql_stack.db_cluster,
  aurora_mysql_stack.sg_rds_client,
  env=APP_ENV
)
sm_notebook_stack.add_dependency(aurora_mysql_stack)

app.synth()
