#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_sagemaker
)
from constructs import Construct

from .utils import name_from_base


class SageMakerRealtimeEndpointStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, execution_role, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    endpoint_name = self.node.try_get_context('sagemaker_endpoint_name')

    endpoint_config = self.node.try_get_context('sagemaker_endpoint_config')
    instance_type = endpoint_config['instance_type']
    managed_instance_scaling = endpoint_config['managed_instance_scaling']
    routing_config = endpoint_config['routing_config']

    sagemaker_endpoint_config = aws_sagemaker.CfnEndpointConfig(self, "EndpointConfig",
      production_variants=[aws_sagemaker.CfnEndpointConfig.ProductionVariantProperty(
        variant_name='AllTraffic',
        initial_instance_count=1,
        instance_type=instance_type,
        managed_instance_scaling=aws_sagemaker.CfnEndpointConfig.ManagedInstanceScalingProperty(
          min_instance_count=managed_instance_scaling['min_instance_count'],
          max_instance_count=managed_instance_scaling['max_instance_count'],
          status=managed_instance_scaling['status'],
        ),
        routing_config=aws_sagemaker.CfnEndpointConfig.RoutingConfigProperty(
          routing_strategy=routing_config['routing_strategy']
        ),
      )],
      endpoint_config_name=name_from_base(f"{endpoint_name}-config"),
      execution_role_arn=execution_role.role_arn,
    )

    self.sagemaker_endpoint = aws_sagemaker.CfnEndpoint(self, "Endpoint",
      endpoint_config_name=sagemaker_endpoint_config.endpoint_config_name,
      endpoint_name=name_from_base(endpoint_name)
    )
    self.sagemaker_endpoint.add_dependency(sagemaker_endpoint_config)

    self.sagemaker_endpoint_variant_name = sagemaker_endpoint_config.production_variants[0].variant_name

    cdk.CfnOutput(self, 'EndpointConfigName',
      value=self.sagemaker_endpoint.endpoint_config_name,
      export_name=f'{self.stack_name}-EndpointConfigName')
    cdk.CfnOutput(self, 'EndpointName',
      value=self.sagemaker_endpoint.endpoint_name,
      export_name=f'{self.stack_name}-EndpointName')
