#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  AuroraMysqlStack,
  NLBforAuroraRDSStack,
  NLBTargetUpdaterLambdaStack
)

APP_ENV = cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')
)

app = cdk.App()

vpc_stack = VpcStack(app, 'AuroraMySQLVpcStack',
  env=APP_ENV)

aurora_mysql_stack = AuroraMysqlStack(app, 'AuroraMySQLStack',
  vpc_stack.vpc,
  env=APP_ENV
)
aurora_mysql_stack.add_dependency(vpc_stack)

nlb_for_aurora_rds_stack = NLBforAuroraRDSStack(app, 'NLBforAuroraRDSStack',
  vpc_stack.vpc,
  aurora_mysql_stack.db_cluster,
  aurora_mysql_stack.sg_mysql_client,
  env=APP_ENV
)
nlb_for_aurora_rds_stack.add_dependency(aurora_mysql_stack)

nlb_target_updater_lambda_stack = NLBTargetUpdaterLambdaStack(app, 'NLBTargetUpdaterLambdaStack',
  aurora_mysql_stack.db_cluster,
  nlb_for_aurora_rds_stack.target_group,
  env=APP_ENV
)
nlb_target_updater_lambda_stack.add_dependency(nlb_for_aurora_rds_stack)

app.synth()
