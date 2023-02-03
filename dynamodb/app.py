#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_dynamodb
)
from constructs import Construct

class DynamodbStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    # vpc_name = self.node.try_get_context('vpc_name')
    # vpc = aws_ec2.Vpc.from_lookup(self, 'DynamodbVPC',
    #   is_default=True,
    #   vpc_name=vpc_name
    # )

    vpc = aws_ec2.Vpc(self, "DynamodbVPC",
      ip_addresses=aws_ec2.IpAddresses.cidr("10.0.0.0/21"),
      max_azs=3,

      # 'subnetConfiguration' specifies the "subnet groups" to create.
      # Every subnet group will have a subnet for each AZ, so this
      # configuration will create `2 groups × 3 AZs = 6` subnets.
      subnet_configuration=[
        {
          "cidrMask": 24,
          "name": "Public",
          "subnetType": aws_ec2.SubnetType.PUBLIC,
        },
        {
          "cidrMask": 24,
          "name": "Private",
          "subnetType": aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
        }
      ],
      gateway_endpoints={
        "DynamoDB": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.DYNAMODB
        )
      }
    )

    #XXX: Another way to add DynamoDB VPC Endpoint
    #dynamo_db_endpoint = vpc.add_gateway_endpoint("DynamoDB",
    #  service=aws_ec2.GatewayVpcEndpointAwsService.DYNAMODB
    #)

    ddb_table = aws_dynamodb.Table(self, "SimpleDynamoDbTable",
      table_name="SimpleTable",
      # removal_policy=cdk.RemovalPolicy.DESTROY,
      partition_key=aws_dynamodb.Attribute(name="pkid",
        type=aws_dynamodb.AttributeType.STRING),
      sort_key=aws_dynamodb.Attribute(name="sortkey",
        type=aws_dynamodb.AttributeType.NUMBER),
      time_to_live_attribute="ttl",
      billing_mode=aws_dynamodb.BillingMode.PROVISIONED,
      read_capacity=15,
      write_capacity=5,
    )


app = cdk.App()
DynamodbStack(app, "dynamodb")

app.synth()
