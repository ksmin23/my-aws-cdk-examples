#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  AuroraMysqlStack,
  NginxRDSProxyStack,
)


APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, "NginxRDSProxyVpcStack",
  env=APP_ENV)

aurora_mysql_stack = AuroraMysqlStack(app, "AuroraMySQLStack",
  vpc_stack.vpc,
  env=APP_ENV)
aurora_mysql_stack.add_dependency(vpc_stack)

rds_proxy_stack = NginxRDSProxyStack(app, "NginxRDSProxyStack",
  vpc_stack.vpc,
  aurora_mysql_stack.sg_rds_client,
  env=APP_ENV
)
rds_proxy_stack.add_dependency(aurora_mysql_stack)

app.synth()
