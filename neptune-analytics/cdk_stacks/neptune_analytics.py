#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk
from aws_cdk import (
  Stack,
  aws_ec2,
  aws_neptunegraph
)
from constructs import Construct


class NeptuneAnalyticsStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    self.neptune_graph_port = int(self.node.try_get_context('neptune_graph_port') or "8182")

    self.sg_neptune_graph_client = aws_ec2.SecurityGroup(self, "NeptuneAnalyticsClientSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for neptune analytics client',
      security_group_name=f'neptune-graph-client-sg-{self.stack_name.lower()}'
    )
    cdk.Tags.of(self.sg_neptune_graph_client).add('Name', 'neptune-graph-client-sg')

    sg_neptune_graph = aws_ec2.SecurityGroup(self, "NeptuneAnalyticsSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for neptune analytics',
      security_group_name=f'neptune-graph-sg-{self.stack_name.lower()}'
    )
    cdk.Tags.of(sg_neptune_graph).add('Name', 'neptune-graph-sg')

    sg_neptune_graph.add_ingress_rule(peer=sg_neptune_graph,
      connection=aws_ec2.Port.tcp(self.neptune_graph_port),
      description='neptune-graph-sg')
    sg_neptune_graph.add_ingress_rule(peer=self.sg_neptune_graph_client,
      connection=aws_ec2.Port.tcp(self.neptune_graph_port),
      description='neptune-graph-client-sg')
    sg_neptune_graph.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(443),
      description='http access')

    self.neptune_graph = aws_neptunegraph.CfnGraph(self, "NeptuneGraph",
      provisioned_memory=128,
      deletion_protection=False,
      public_connectivity=False,
      replica_count=1,
      vector_search_configuration=aws_neptunegraph.CfnGraph.VectorSearchConfigurationProperty(
        vector_search_dimension=1536
      )
    )

    neptune_graph_private_endpoint = aws_neptunegraph.CfnPrivateGraphEndpoint(self, "NeptuneGraphPrivateEndpoint",
      graph_identifier=self.neptune_graph.attr_graph_id,
      vpc_id=vpc.vpc_id,

      security_group_ids=[sg_neptune_graph.security_group_id],
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
    )
    neptune_graph_private_endpoint.add_dependency(self.neptune_graph)

    self.neptune_graph_subnet_ids = neptune_graph_private_endpoint.subnet_ids


    cdk.CfnOutput(self, 'NAGraphEndpoint',
      value=self.neptune_graph.attr_endpoint,
      export_name=f'{self.stack_name}-Endpoint')
    cdk.CfnOutput(self, 'NAGraphPort',
      value=f'{self.neptune_graph_port}',
      export_name=f'{self.stack_name}-Port')
    cdk.CfnOutput(self, 'NAGraphId',
      value=self.neptune_graph.attr_graph_id,
      export_name=f'{self.stack_name}-GraphId')
    cdk.CfnOutput(self, 'NAGraphName',
      value=f'{self.neptune_graph.graph_name}',
      export_name=f'{self.stack_name}-GraphName')
    cdk.CfnOutput(self, 'NAGraphClientSecurityGroupId',
      value=self.sg_neptune_graph_client.security_group_id,
      export_name=f'{self.stack_name}-ClientSecurityGroupId')
