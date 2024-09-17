#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  NeptuneServerlessStack,
  SageMakerNotebookStack
)

APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)


app = cdk.App()

vpc_stack = VpcStack(app, 'NeptuneServerlessVpcStack',
  env=APP_ENV)

neptune_serverless_stack = NeptuneServerlessStack(app, 'NeptuneServerlessStack',
  vpc_stack.vpc,
  env=APP_ENV)
neptune_serverless_stack.add_dependency(vpc_stack)

neptune_serverless_workbench = SageMakerNotebookStack(app, 'NeptuneServerlessWorkbenchStack',
  neptune_serverless_stack.graph_db,
  neptune_serverless_stack.sg_graph_db_client,
  neptune_serverless_stack.graph_db_subnet_group,
  env=APP_ENV
)
neptune_serverless_workbench.add_dependency(neptune_serverless_stack)

app.synth()
