#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  DocumentdbStack,
  SageMakerNotebookStack
)


AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, 'AmazonDocDBVpcStack',
  env=AWS_ENV
)

docdb_stack = DocumentdbStack(app, 'AmazonDocDBStack',
  vpc_stack.vpc,
  env=AWS_ENV
)
docdb_stack.add_dependency(vpc_stack)

sm_notebook = SageMakerNotebookStack(app, 'AmazonDocDBWorkbenchStack',
  vpc_stack.vpc,
  docdb_stack.docdb_cluster,
  docdb_stack.sg_docdb_client,
  env=AWS_ENV
)
sm_notebook.add_dependency(docdb_stack)

app.synth()