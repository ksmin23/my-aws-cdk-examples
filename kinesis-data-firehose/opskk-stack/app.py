#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

from cdk_stacks import (
  VpcStack,
  OpenSearchDomainStack,
  BastionHostEC2InstanceStack,
  KinesisFirehoseStack
)

import aws_cdk as cdk


AWS_ENV = cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')
)

app = cdk.App()

vpc_stack = VpcStack(app, "OpenSearchFirehoseKibanaVpcStack",
  env=AWS_ENV
)

ops_domain_stack = OpenSearchDomainStack(app, "OpenSearchDomainStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
ops_domain_stack.add_dependency(vpc_stack)

firehose_stack = KinesisFirehoseStack(app, "FirehoseToOpsDomainStack",
  vpc_stack.vpc,
  ops_domain_stack.opensearch_domain,
  ops_domain_stack.opensearch_index_name,
  ops_domain_stack.sg_opensearch_client,
  env=AWS_ENV
)
firehose_stack.add_dependency(ops_domain_stack)

bastion_host = BastionHostEC2InstanceStack(app, "OpsClientEC2Stack",
  vpc_stack.vpc,
  ops_domain_stack.sg_opensearch_client,
  env=AWS_ENV
)
bastion_host.add_dependency(firehose_stack)

app.synth()
