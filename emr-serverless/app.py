#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_emrserverless,
)
from constructs import Construct

class EmrServerlessStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    EMR_SERVERLESS_APP_NAME = cdk.CfnParameter(self, 'EMRServerlessAppName',
      type='String',
      description='Amazon EMR Serverless Application name',
      default='my-spark-app'
    )

    emr_serverless_app = aws_emrserverless.CfnApplication(self, "MyEmrServerlessApp",
      release_label="emr-6.6.0",
      type="Spark",

      # the properties below are optional
      auto_start_configuration=aws_emrserverless.CfnApplication.AutoStartConfigurationProperty(
        enabled=True
      ),
      auto_stop_configuration=aws_emrserverless.CfnApplication.AutoStopConfigurationProperty(
        enabled=True,
        idle_timeout_minutes=15
      ),
      initial_capacity=[aws_emrserverless.CfnApplication.InitialCapacityConfigKeyValuePairProperty(
        key="Driver",
        value=aws_emrserverless.CfnApplication.InitialCapacityConfigProperty(
          worker_configuration=aws_emrserverless.CfnApplication.WorkerConfigurationProperty(
            cpu="2vCPU",
            memory="4GB"
          ),
          worker_count=2
        )
      ),
      aws_emrserverless.CfnApplication.InitialCapacityConfigKeyValuePairProperty(
        key="Executor",
        value=aws_emrserverless.CfnApplication.InitialCapacityConfigProperty(
          worker_configuration=aws_emrserverless.CfnApplication.WorkerConfigurationProperty(
            cpu="4vCPU",
            memory="8GB"
          ),
          worker_count=10
        )
      )],
      maximum_capacity=aws_emrserverless.CfnApplication.MaximumAllowedResourcesProperty(
        cpu="200vCPU",
        memory="200GB",
        disk="1000GB"
      ),
      name=EMR_SERVERLESS_APP_NAME.value_as_string
    )


app = cdk.App()
EmrServerlessStack(app, "EmrServerlessStack",
  env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
