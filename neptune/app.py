#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  NeptuneStack,
  SageMakerNotebookStack
)

APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)


app = cdk.App()

vpc_stack = VpcStack(app, 'NeptuneVpcStack',
  env=APP_ENV)

neptune_stack = NeptuneStack(app, 'NeptuneStack',
  vpc_stack.vpc,
  env=APP_ENV)
neptune_stack.add_dependency(vpc_stack)

neptune_workbench = SageMakerNotebookStack(app, 'NeptuneWorkbenchStack',
  neptune_stack.graph_db,
  neptune_stack.sg_graph_db_client,
  neptune_stack.graph_db_subnet_group,
  env=APP_ENV
)
neptune_workbench.add_dependency(neptune_stack)

app.synth()
