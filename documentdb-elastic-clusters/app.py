#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

from cdk_stacks import (
  VpcStack,
  DocDBClientEC2InstanceStack,
  DocumentDbElasticClustersStack
)

import aws_cdk as cdk


AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

vpc_stack = VpcStack(app, 'DocDBElasticVpc',
  env=AWS_ENV)

docdb_elastic_cluster_stack = DocumentDbElasticClustersStack(app, 'DocDBElasticStack',
  vpc_stack.vpc,
  env=AWS_ENV
)
docdb_elastic_cluster_stack.add_dependency(vpc_stack)

docdb_client_ec2_stack = DocDBClientEC2InstanceStack(app, 'DocDBClientEC2Instance',
  vpc_stack.vpc,
  docdb_elastic_cluster_stack.sg_docdb_client,
  env=AWS_ENV
)
docdb_client_ec2_stack.add_dependency(docdb_elastic_cluster_stack)

app.synth()
