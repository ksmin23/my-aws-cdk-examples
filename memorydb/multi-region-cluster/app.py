#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  MemoryDBMultiRegionClusterStack
)


APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

memdb_multi_region_cluster = MemoryDBMultiRegionClusterStack(
  app, 'MemoryDBMultiRegionClusterStack',
  env=APP_ENV)

app.synth()
