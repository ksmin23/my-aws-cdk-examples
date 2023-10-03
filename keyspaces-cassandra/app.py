#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  BastionHostEC2InstanceStack,
  KeyspaceStack,
  KeyspaceTableStack
)

AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, 'KeyspaceVpcStack',
  env=AWS_ENV)

keyspace_host = BastionHostEC2InstanceStack(app, 'KeyspaceClientHost',
  vpc_stack.vpc,
  env=AWS_ENV
)
keyspace_host.add_dependency(vpc_stack)

keyspace = KeyspaceStack(app, 'KeyspaceCassandra'
  # ,env=AWS_ENV
)
keyspace.add_dependency(keyspace_host)

keyspace_tables = KeyspaceTableStack(app, 'KeyspaceTables'
  # ,env=AWS_ENV
)
keyspace_tables.add_dependency(keyspace)

app.synth()

