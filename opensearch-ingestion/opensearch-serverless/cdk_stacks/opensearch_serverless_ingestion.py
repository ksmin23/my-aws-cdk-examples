#!/usr/bin/env python3
import json

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_osis,
  aws_opensearchserverless as aws_opss
)
from constructs import Construct


class OpsServerlessIngestionStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, collection_endpoint, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    pipeline_name = "serverless-ingestion"

    pipeline_configuration_body = f'''version: "2"
log-pipeline:
  source:
    http:
      path: "/${{pipelineName}}/test_ingestion_path"
  processor:
    - date:
        from_time_received: true
        destination: "@timestamp"
  sink:
    - opensearch:
        hosts: [ "{collection_endpoint}" ]
        index: "my_logs"
        aws:
          sts_role_arn: "arn:aws:iam::{cdk.Aws.ACCOUNT_ID}:role/PipelineRole"
          region: "{cdk.Aws.REGION}"
          serverless: true'''

    cfn_pipeline = aws_osis.CfnPipeline(self, "CfnOSISPipeline",
      max_units=4,
      min_units=1,
      pipeline_configuration_body=pipeline_configuration_body,
      pipeline_name=pipeline_name,

      # the properties below are optional
      log_publishing_options=aws_osis.CfnPipeline.LogPublishingOptionsProperty(
        cloud_watch_log_destination=aws_osis.CfnPipeline.CloudWatchLogDestinationProperty(
          log_group=f"/aws/vendedlogs/OpenSearchIngestion/{pipeline_name}/audit-logs"
        ),
        is_logging_enabled=False
      )
    )
