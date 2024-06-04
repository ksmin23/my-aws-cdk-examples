#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Duration,
  Stack,
  aws_applicationautoscaling as aws_appscaling,
  aws_cloudwatch
)
from constructs import Construct


class SageMakerAsyncEndpointAutoScalingStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, sagemaker_endpoint, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    RESOURCE_ID = f"endpoint/{sagemaker_endpoint.cfn_endpoint.endpoint_name}/variant/AllTraffic"
    MAX_CAPACITY = self.node.try_get_context('max_capacity') or 3

    #XXX: For more information, see
    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html
    autoscale_target = aws_appscaling.ScalableTarget(self, "SageMakerVariantScalableTarget",
      service_namespace=aws_appscaling.ServiceNamespace.SAGEMAKER,
      scalable_dimension="sagemaker:variant:DesiredInstanceCount",
      min_capacity=0,
      max_capacity=MAX_CAPACITY,
      resource_id=RESOURCE_ID
    )

    #XXX: If you want to see an example of autoscaling policy, see
    # https://github.com/aws/amazon-sagemaker-examples/blob/main/async-inference/Async-Inference-Walkthrough.ipynb
    autoscale_target.scale_to_track_metric("SageMakerAsyncInvocations",
      policy_name='Invocations-ScalingPolicy',
      target_value=5.0, # The target value for the metric. - here the metric is - SageMakerVariantInvocationsPerInstance
      custom_metric=aws_cloudwatch.Metric(
        metric_name='ApproximateBacklogSizePerInstance',
        namespace='AWS/SageMaker',
        dimensions_map={
          'EndpointName': sagemaker_endpoint.cfn_endpoint.endpoint_name
        },
        statistic=aws_cloudwatch.Stats.AVERAGE
      ),
      scale_in_cooldown=Duration.seconds(60),
      scale_out_cooldown=Duration.seconds(60)
    )

    cdk.CfnOutput(self, 'AppScalingResourceId',
      value=RESOURCE_ID,
      export_name=f'{self.stack_name}-AppScalingResourceId')
    cdk.CfnOutput(self, 'AppScalingTargetId',
      value=autoscale_target.scalable_target_id,
      export_name=f'{self.stack_name}-AppScalingTargetId')
