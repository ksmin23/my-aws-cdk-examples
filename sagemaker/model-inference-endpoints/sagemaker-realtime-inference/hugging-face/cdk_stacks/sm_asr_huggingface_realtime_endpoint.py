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
  HuggingFaceSageMakerEndpoint,
  DeepLearningContainerImage,
  SageMakerInstanceType,
)

random.seed(37)


def name_from_base(base, max_length=63):
  unique = ''.join(random.sample(string.digits, k=7))
  max_length = 63
  trimmed_base = base[: max_length - len(unique) - 1]
  return "{}-{}".format(trimmed_base, unique)


class ASRHuggingFaceRealtimeEndpointStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    model_id = self.node.try_get_context('model_id') or 'openai/whisper-medium'
    sagemaker_endpoint_name = name_from_base(model_id.replace('/', '-').replace('.', '-'))

    self.sagemaker_endpoint = HuggingFaceSageMakerEndpoint(self, 'HFSageMakerEndpoint',
      model_id=model_id,
      instance_type=SageMakerInstanceType.ML_G5_2_XLARGE,
      # XXX: Available Deep Learing Container (DLC) Image List
      # https://github.com/awslabs/generative-ai-cdk-constructs/blob/main/src/patterns/gen-ai/aws-model-deployment-sagemaker/deep-learning-container-image.ts
      container=DeepLearningContainerImage.HUGGINGFACE_PYTORCH_INFERENCE_2_0_0_TRANSFORMERS4_28_1_GPU_PY310_CU118_UBUNTU20_04,
      endpoint_name=sagemaker_endpoint_name,
      environment={
        #XXX: For more information about the task for a model, see:
        # https://github.com/aws/sagemaker-huggingface-inference-toolkit/blob/main/src/sagemaker_huggingface_inference_toolkit/transformers_utils.py#L272
        'HF_TASK': 'automatic-speech-recognition',

        #XXX: For Async Inference
        # https://docs.aws.amazon.com/sagemaker/latest/dg/async-inference-create-endpoint.html
        # https://discuss.huggingface.co/t/payload-too-large-for-async-inference-on-sagemaker/40717/6
        # 'chunk_length_s': '30',
        # 'MMS_MAX_REQUEST_SIZE': '2000000000',
        # 'MMS_MAX_RESPONSE_SIZE': '2000000000',
        # 'MMS_DEFAULT_RESPONSE_TIMEOUT': '900'
      }
    )


    cdk.CfnOutput(self, 'EndpointName',
      value=self.sagemaker_endpoint.cfn_endpoint.endpoint_name,
      export_name=f'{self.stack_name}-EndpointName')
    cdk.CfnOutput(self, 'EndpointArn',
      value=self.sagemaker_endpoint.endpoint_arn,
      export_name=f'{self.stack_name}-EndpointArn')