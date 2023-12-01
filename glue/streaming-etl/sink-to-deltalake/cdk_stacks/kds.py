#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Duration,
  Stack,
  aws_kinesis,
)
from constructs import Construct

random.seed(23)


class KdsStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    KINESIS_DEFAULT_STREAM_NAME = 'PUT-{}'.format(''.join(random.sample((string.ascii_letters), k=5)))
    KINESIS_STREAM_NAME = self.node.try_get_context('kinesis_stream_name') or KINESIS_DEFAULT_STREAM_NAME

    source_kinesis_stream = aws_kinesis.Stream(self, "SourceKinesisStreams",
      retention_period=Duration.hours(24),
      stream_mode=aws_kinesis.StreamMode.ON_DEMAND,
      stream_name=KINESIS_STREAM_NAME)

    self.kinesis_stream = source_kinesis_stream

    cdk.CfnOutput(self, f'{self.stack_name}_KinesisDataStreamName', value=self.kinesis_stream.stream_name)

