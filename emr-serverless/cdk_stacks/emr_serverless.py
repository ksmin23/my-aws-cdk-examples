#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_emrserverless,
  aws_iam
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

    emr_serverless_s3_and_glue_access_policy_doc = aws_iam.PolicyDocument()

    emr_serverless_s3_and_glue_access_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "ReadAccessForEMRSamples",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "resources": [
        "arn:aws:s3:::*.elasticmapreduce",
        "arn:aws:s3:::*.elasticmapreduce/*"
      ]
    }))

    emr_serverless_s3_and_glue_access_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "FullAccessToOutputBucket",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "resources": [
        "arn:aws:s3:::*deltalake*",
        "arn:aws:s3:::*deltalake*/*"
      ]
    }))

    emr_serverless_s3_and_glue_access_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "GlueCreateAndReadDataCatalog",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "glue:GetDatabase",
        "glue:CreateDatabase",
        "glue:GetDataBases",
        "glue:CreateTable",
        "glue:GetTable",
        "glue:UpdateTable",
        "glue:DeleteTable",
        "glue:GetTables",
        "glue:GetPartition",
        "glue:GetPartitions",
        "glue:CreatePartition",
        "glue:BatchCreatePartition",
        "glue:GetUserDefinedFunctions"
      ],
      "resources": [
        "*"
      ]
    }))

    emr_serverless_s3_runtime_role = aws_iam.Role(self, 'EmrServerlessS3RuntimeRole',
      role_name='EMRServerlessS3RuntimeRole',
      assumed_by=aws_iam.ServicePrincipal('elasticmapreduce.amazonaws.com'),
      inline_policies={
        'EMRServerlessS3AndGlueAccessPolicy': emr_serverless_s3_and_glue_access_policy_doc
      }
    )

    emr_version = self.node.try_get_context('emr_version') or "emr-7.2.0"
    emr_serverless_app = aws_emrserverless.CfnApplication(self, "MyEmrServerlessApp",
      release_label=emr_version,
      type="Spark",

      # the properties below are optional
      auto_start_configuration=aws_emrserverless.CfnApplication.AutoStartConfigurationProperty(
        enabled=True
      ),
      auto_stop_configuration=aws_emrserverless.CfnApplication.AutoStopConfigurationProperty(
        enabled=True,
        idle_timeout_minutes=360
      ),
      initial_capacity=[aws_emrserverless.CfnApplication.InitialCapacityConfigKeyValuePairProperty(
        key="Driver",
        value=aws_emrserverless.CfnApplication.InitialCapacityConfigProperty(
          worker_configuration=aws_emrserverless.CfnApplication.WorkerConfigurationProperty(
            cpu="4vCPU",
            memory="16GB",

            # the properties below are optional
            disk="32GB"
          ),
          worker_count=2
        )
      ),
      aws_emrserverless.CfnApplication.InitialCapacityConfigKeyValuePairProperty(
        key="Executor",
        value=aws_emrserverless.CfnApplication.InitialCapacityConfigProperty(
          worker_configuration=aws_emrserverless.CfnApplication.WorkerConfigurationProperty(
            cpu="4vCPU",
            memory="16GB",

            # the properties below are optional
            disk="32GB"
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


    cdk.CfnOutput(self, 'ApplicationName', value=emr_serverless_app.name,
      export_name=f'{self.stack_name}-ApplicationName')
    cdk.CfnOutput(self, 'EMRServerlessApplicationId', value=emr_serverless_app.attr_application_id,
      export_name=f'{self.stack_name}-ApplicationId')
    cdk.CfnOutput(self, 'EMRServerlessReleaseLabel', value=emr_serverless_app.release_label,
      export_name=f'{self.stack_name}-ReleaseLabel')
