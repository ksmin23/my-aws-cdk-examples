#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  SageMakerExecutionRoleStack,
  SageMakerHuggingFaceModelStack,
  SageMakerRealtimeEndpointStack,
  SageMakerInferenceComponentStack
)


APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

sm_execution_role = SageMakerExecutionRoleStack(app, 'SageMakerExecutionRoleStack',
  env=APP_ENV
)

sm_endpoint = SageMakerRealtimeEndpointStack(app, 'SageMakerRealtimeEndpointStack',
  execution_role=sm_execution_role.sagemaker_execution_role,
  env=APP_ENV
)
sm_endpoint.add_dependency(sm_execution_role)

sm_model_1 = SageMakerHuggingFaceModelStack(app, 'SageMakerHuggingFaceModel1',
  model_id="dolly-v2-7b",
  execution_role=sm_execution_role.sagemaker_execution_role,
  env=APP_ENV
)
sm_model_1.add_dependency(sm_endpoint)

sm_model_2 = SageMakerHuggingFaceModelStack(app, 'SageMakerHuggingFaceModel2',
  model_id="flan-t5-xxl",
  execution_role=sm_execution_role.sagemaker_execution_role,
  env=APP_ENV
)
sm_model_2.add_dependency(sm_model_1)

sm_inference_component_1 = SageMakerInferenceComponentStack(app, 'SageMakerInferenceComponent1',
  inference_component_name="ic-dolly-v2-7b",
  model_name=sm_model_1.model.model_name,
  endpoint_name=sm_endpoint.sagemaker_endpoint.endpoint_name,
  variant_name=sm_endpoint.sagemaker_endpoint_variant_name,
  env=APP_ENV
)
sm_inference_component_1.add_dependency(sm_model_2)

sm_inference_component_2 = SageMakerInferenceComponentStack(app, 'SageMakerInferenceComponent2',
  inference_component_name="ic-flan-t5-xxl",
  model_name=sm_model_2.model.model_name,
  endpoint_name=sm_endpoint.sagemaker_endpoint.endpoint_name,
  variant_name=sm_endpoint.sagemaker_endpoint_variant_name,
  env=APP_ENV
)
sm_inference_component_2.add_dependency(sm_inference_component_1)

app.synth()