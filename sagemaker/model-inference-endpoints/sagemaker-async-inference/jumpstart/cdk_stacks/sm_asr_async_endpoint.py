#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam,
  aws_s3 as s3,
  aws_sns
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


class ASRAsyncEndpointStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    async_inference_error_sns_topic = aws_sns.Topic(self, 'AsyncInferErrorSNSTopic',
      topic_name='AsyncInferError',
      display_name='Asynchronous Inference Error Topic'
    )

    async_inference_success_sns_topic = aws_sns.Topic(self, 'AsyncInferSuccessSNSTopic',
      topic_name='AsyncInferSuccess',
      display_name='Asynchronous Inference Success Topic'
    )

    S3_DEFAULT_BUCKET_NAME = f'sagemaker-async-inference-{kwargs['env'].region}-{kwargs['env'].account}'
    s3_output_bucket_name = self.node.try_get_context('s3_output_bucket_name') or S3_DEFAULT_BUCKET_NAME
    s3_output_bucket = s3.Bucket(self, "s3bucket",
      bucket_name=s3_output_bucket_name,
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: core.RemovalPolicy.RETAIN - The bucket will be orphaned
      auto_delete_objects=True)

    sagemaker_execution_policy_doc = aws_iam.PolicyDocument()
    sagemaker_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [
        self.format_arn(service="sns", region=cdk.Aws.REGION, resource=async_inference_success_sns_topic.topic_name),
        self.format_arn(service="sns", region=cdk.Aws.REGION, resource=async_inference_error_sns_topic.topic_name),
      ],
      "actions": [
        "sns:Publish"
      ]
    }))

    sagemaker_execution_role = aws_iam.Role(self, 'SageMakerEndpointRole',
      role_name=f'AmazonSageMakerEndpointRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      path='/',
      inline_policies={
        'sagemaker-execution-policy': sagemaker_execution_policy_doc,
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerFullAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSNSReadOnlyAccess')
      ]
    )

    jumpstart_model = self.node.try_get_context('jumpstart_model_info')
    model_id, model_version = jumpstart_model.get('model_id', 'huggingface-asr-whisper-medium'), jumpstart_model.get('version', '3.0.0')
    model_name = f"{model_id.upper().replace('-', '_')}_{model_version.replace('.', '_')}"

    sagemaker_endpoint_name = name_from_base(model_id.replace('/', '-').replace('.', '-'))

    #XXX: Available JumStart Model List
    # https://github.com/awslabs/generative-ai-cdk-constructs/blob/main/src/patterns/gen-ai/aws-model-deployment-sagemaker/jumpstart-model.ts
    self.sagemaker_endpoint = JumpStartSageMakerEndpoint(self, 'SageMakerEndpoint',
      model=JumpStartModel.of(model_name),
      endpoint_name=sagemaker_endpoint_name,
      accept_eula=True,
      instance_type=SageMakerInstanceType.ML_G5_2_XLARGE,
      role=sagemaker_execution_role
    )

    s3_failure_path = f"s3://{s3_output_bucket.bucket_name}/{self.stack_name.lower()}/error"
    s3_output_path = f"s3://{s3_output_bucket.bucket_name}/{self.stack_name.lower()}/output"

    async_inference_config = {
      'OutputConfig': {
        'NotificationConfig': {
          'ErrorTopic': async_inference_error_sns_topic.topic_arn,
          'SuccessTopic': async_inference_success_sns_topic.topic_arn
        },
        'S3FailurePath': s3_failure_path,
        'S3OutputPath': s3_output_path
      },
      'ClientConfig': {
        'MaxConcurrentInvocationsPerInstance': 4
      }
    }

    self.sagemaker_endpoint.cfn_endpoint_config.add_override(
      'Properties.AsyncInferenceConfig', async_inference_config
    )


    cdk.CfnOutput(self, 'EndpointName',
      value=self.sagemaker_endpoint.cfn_endpoint.endpoint_name,
      export_name=f'{self.stack_name}-EndpointName')
    cdk.CfnOutput(self, 'EndpointArn',
      value=self.sagemaker_endpoint.endpoint_arn,
      export_name=f'{self.stack_name}-EndpointArn')