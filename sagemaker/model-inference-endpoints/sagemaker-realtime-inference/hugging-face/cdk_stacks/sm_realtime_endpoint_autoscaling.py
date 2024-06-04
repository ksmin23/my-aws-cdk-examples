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


class SageMakerRealtimeEndpointAutoScalingStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, sagemaker_endpoint, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For more information, see
    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html
    autoscale_target = aws_appscaling.ScalableTarget(self, "SageMakerVariantScalableTarget",
      service_namespace=aws_appscaling.ServiceNamespace.SAGEMAKER,
      scalable_dimension="sagemaker:variant:DesiredInstanceCount",
      min_capacity=1,
      max_capacity=4,
      resource_id=f"endpoint/{sagemaker_endpoint.cfn_endpoint.endpoint_name}/variant/AllTraffic"
    )

    #XXX: If you want to see an example of autoscaling policy, see
    # https://github.com/aws/amazon-sagemaker-examples/blob/main/multi-model-endpoints/mme-on-gpu/cv/resnet50_mme_with_gpu.ipynb
    autoscale_target.scale_to_track_metric("SageMakerVariantGPUUtilPerInstance",
      policy_name='GPUUtil-ScalingPolicy',
      target_value=70.0,
      custom_metric=aws_cloudwatch.Metric(
        metric_name='GPUUtilization',
        namespace='/aws/sagemaker/Endpoints',
        dimensions_map={
          'VariantName': 'AllTraffic'
        },
        statistic=aws_cloudwatch.Stats.AVERAGE,
        unit=aws_cloudwatch.Unit.PERCENT
      ),
      scale_in_cooldown=Duration.seconds(600),
      scale_out_cooldown=Duration.seconds(200)
    )


    cdk.CfnOutput(self, 'AppScalingTargetId',
      value=autoscale_target.scalable_target_id,
      export_name=f'{self.stack_name}-AppScalingTargetId')
