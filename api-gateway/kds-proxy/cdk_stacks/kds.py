#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_kinesis
)
from constructs import Construct

random.seed(47)


class KinesisDataStreamsStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    KINESIS_STREAM_NAME = cdk.CfnParameter(self, 'KinesisStreamName',
      type='String',
      description='kinesis data stream name',
      default='PUT-Firehose-{}'.format(''.join(random.sample((string.ascii_letters), k=5)))
    )

    self.kinesis_stream = aws_kinesis.Stream(self, "SourceKinesisStreams",
      retention_period=cdk.Duration.hours(24),
      stream_mode=aws_kinesis.StreamMode.ON_DEMAND,
      stream_name=KINESIS_STREAM_NAME.value_as_string)


    cdk.CfnOutput(self, 'KinesisDataStreamsName',
      value=self.kinesis_stream.stream_name,
      export_name=f'{self.stack_name}-KinesisDataStreamsName')
