#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  NeptuneAnalyticsStack,
  SageMakerNotebookStack,
  VpcStack
)


APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, 'NeptuneAnalyticsVpcStack',
  env=APP_ENV)

neptune_analytics_stack = NeptuneAnalyticsStack(app, 'NeptuneAnalyticsStack',
  vpc_stack.vpc,
  env=APP_ENV)
neptune_analytics_stack.add_dependency(vpc_stack)

neptune_analytics_workbench = SageMakerNotebookStack(app, 'NeptuneAnalyticsWorkbenchStack',
  neptune_analytics_stack.neptune_graph,
  neptune_analytics_stack.neptune_graph_port,
  neptune_analytics_stack.sg_neptune_graph_client,
  neptune_analytics_stack.neptune_graph_subnet_ids,
  env=APP_ENV
)
neptune_analytics_workbench.add_dependency(neptune_analytics_stack)

app.synth()
