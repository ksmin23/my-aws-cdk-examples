#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
)
from constructs import Construct

from cdklabs.generative_ai_cdk_constructs import (
  JumpStartSageMakerEndpoint,
  JumpStartModel,
  SageMakerInstanceType
)

random.seed(47)


def name_from_base(base, max_length=63):
  unique = ''.join(random.sample(string.digits, k=7))
  max_length = 63
  trimmed_base = base[: max_length - len(unique) - 1]
  return "{}-{}".format(trimmed_base, unique)


class ASRRealtimeEndpointStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    jumpstart_model = self.node.try_get_context('jumpstart_model_info')
    model_id, model_version = jumpstart_model.get('model_id', 'huggingface-asr-whisper-medium'), jumpstart_model.get('version', '3.0.0')
    model_name = f"{model_id.upper().replace('-', '_')}_{model_version.replace('.', '_')}"

    sagemaker_endpoint_name = name_from_base(model_id.replace('/', '-').replace('.', '-'))

    #XXX: Available JumStart Model List
    # https://github.com/awslabs/generative-ai-cdk-constructs/blob/main/src/patterns/gen-ai/aws-model-deployment-sagemaker/jumpstart-model.ts
    self.sagemaker_endpoint = JumpStartSageMakerEndpoint(self, 'JumpStartSageMakerEndpoint',
      model=JumpStartModel.of(model_name),
      accept_eula=True,
      instance_type=SageMakerInstanceType.ML_G5_2_XLARGE,
      endpoint_name=sagemaker_endpoint_name
    )


    cdk.CfnOutput(self, 'EndpointName',
      value=self.sagemaker_endpoint.cfn_endpoint.endpoint_name,
      export_name=f'{self.stack_name}-EndpointName')
    cdk.CfnOutput(self, 'EndpointArn',
      value=self.sagemaker_endpoint.endpoint_arn,
      export_name=f'{self.stack_name}-EndpointArn')