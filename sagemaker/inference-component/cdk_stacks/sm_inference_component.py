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


class SageMakerInferenceComponentStack(Stack):

  def __init__(self, scope: Construct, construct_id: str,
              inference_component_name: str,
              model_name: str,
              endpoint_name: str,
              variant_name: str,
              **kwargs) -> None:

    super().__init__(scope, construct_id, **kwargs)

    inference_component_list = self.node.try_get_context('inference_components')
    inference_component_config = inference_component_list[inference_component_name]
    runtime_config = inference_component_config['runtime_config']
    compute_resource_requirements = inference_component_config['compute_resource_requirements']

    cfn_inference_component = aws_sagemaker.CfnInferenceComponent(self, "CfnInferenceComponent",
      inference_component_name=name_from_base(inference_component_name),
      endpoint_name=endpoint_name,
      variant_name=variant_name,
      runtime_config=aws_sagemaker.CfnInferenceComponent.InferenceComponentRuntimeConfigProperty(
        copy_count=runtime_config['copy_count']
      ),
      specification=aws_sagemaker.CfnInferenceComponent.InferenceComponentSpecificationProperty(
        model_name=model_name,
        compute_resource_requirements=aws_sagemaker.CfnInferenceComponent.InferenceComponentComputeResourceRequirementsProperty(
          number_of_accelerator_devices_required=compute_resource_requirements['number_of_accelerator_devices_required'],
          number_of_cpu_cores_required=compute_resource_requirements['number_of_cpu_cores_required'],
          min_memory_required_in_mb=compute_resource_requirements['min_memory_required_in_mb'],
        ),
      ),
    )

    cdk.CfnOutput(self, 'InferenceComponentName',
      value=cfn_inference_component.inference_component_name,
      export_name=f'{self.stack_name}-InferenceComponentName')
    cdk.CfnOutput(self, 'EndpointName',
      value=cfn_inference_component.endpoint_name,
      export_name=f'{self.stack_name}-EndpointName')