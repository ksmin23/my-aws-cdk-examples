#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  OpensearchStack,
  BastionHostEC2InstanceStack,
)

APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)


app = cdk.App()

vpc_stack = VpcStack(app, 'OpensearchVpcStack',
  env=APP_ENV)

opensearch_stack = OpensearchStack(app, 'OpensearchCfnDomainStack',
  vpc_stack.vpc,
  env=APP_ENV)
opensearch_stack.add_dependency(opensearch_stack)

bastion_host = BastionHostEC2InstanceStack(app, 'OpesearchBastionHost',
  vpc_stack.vpc,
  opensearch_stack.sg_opensearch_client,
  env=APP_ENV
)
bastion_host.add_dependency(opensearch_stack)

app.synth()
