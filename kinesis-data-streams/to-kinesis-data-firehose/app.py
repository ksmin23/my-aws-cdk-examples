#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  KinesisDataStreamsStack,
  KinesisFirehoseStack
)


AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

kds_stack = KinesisDataStreamsStack(app, "KinesisDataStreamsStack",
  env=AWS_ENV
)

firehose_stack = KinesisFirehoseStack(app, "FirehoseFromKinesisStreamsToS3Stack",
  kds_stack.source_kinesis_stream,
  env=AWS_ENV
)
firehose_stack.add_dependency(kds_stack)

app.synth()
