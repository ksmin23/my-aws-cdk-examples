#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2
)
from constructs import Construct


class VpcStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    vpc_name = self.node.try_get_context("vpc_name") or "default"
    self.vpc = aws_ec2.Vpc.from_lookup(self, 'Ec2WithUserDataStackVPC',
      is_default=True,
      vpc_name=vpc_name)


    #XXX: The Name field of every Export member must be specified and consist only of alphanumeric characters, colons, or hyphens.
    cdk.CfnOutput(self, 'VPCID', value=self.vpc.vpc_id,
      export_name=f'{self.stack_name}-VPCID')

