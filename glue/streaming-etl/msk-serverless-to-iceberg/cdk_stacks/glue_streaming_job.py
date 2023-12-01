#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_glue
)
from constructs import Construct


class GlueStreamingJobStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, glue_job_role, msk_connection_info, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    glue_assets_s3_bucket_name = self.node.try_get_context('glue_assets_s3_bucket_name')
    glue_job_script_file_name = self.node.try_get_context('glue_job_script_file_name')
    glue_job_input_arguments = self.node.try_get_context('glue_job_input_arguments')

    msk_connection_name = msk_connection_info.name
    kafka_bootstrap_servers = msk_connection_info.connection_properties['KAFKA_BOOTSTRAP_SERVERS']

    glue_job_default_arguments = {
      "--enable-metrics": "true",
      "--enable-spark-ui": "true",
      "--spark-event-logs-path": f"s3://{glue_assets_s3_bucket_name}/sparkHistoryLogs/",
      "--enable-job-insights": "false",
      "--enable-glue-datacatalog": "true",
      "--enable-continuous-cloudwatch-log": "true",
      "--job-bookmark-option": "job-bookmark-disable",
      "--job-language": "python",
      "--TempDir": f"s3://{glue_assets_s3_bucket_name}/temporary/",
      "--kafka_connection_name": msk_connection_name,
      "--kafka_bootstrap_servers": kafka_bootstrap_servers,
    }

    glue_job_default_arguments.update(glue_job_input_arguments)

    glue_job_name = self.node.try_get_context('glue_job_name')

    glue_connections_name = self.node.try_get_context('glue_connections_name')

    glue_cfn_job = aws_glue.CfnJob(self, "GlueStreamingETLJob",
      command=aws_glue.CfnJob.JobCommandProperty(
        name="gluestreaming",
        python_version="3",
        script_location="s3://{glue_assets}/scripts/{glue_job_script_file_name}".format(
          glue_assets=glue_assets_s3_bucket_name,
          glue_job_script_file_name=glue_job_script_file_name
        )
      ),
      role=glue_job_role.role_arn,

      #XXX: Set only AllocatedCapacity or MaxCapacity
      # Do not set Allocated Capacity if using Worker Type and Number of Workers
      # allocated_capacity=2,
      connections=aws_glue.CfnJob.ConnectionsListProperty(
        connections=[glue_connections_name, msk_connection_name]
      ),
      default_arguments=glue_job_default_arguments,
      description="This job loads the data from MSK to Apache Iceberg table in S3.",
      execution_property=aws_glue.CfnJob.ExecutionPropertyProperty(
        max_concurrent_runs=1
      ),
      #XXX: check AWS Glue Version in https://docs.aws.amazon.com/glue/latest/dg/add-job.html#create-job
      glue_version="3.0",
      #XXX: Do not set Max Capacity if using Worker Type and Number of Workers
      # max_capacity=2,
      max_retries=0,
      name=glue_job_name,
      # notification_property=aws_glue.CfnJob.NotificationPropertyProperty(
      #   notify_delay_after=10 # 10 minutes
      # ),
      number_of_workers=2,
      timeout=2880,
      worker_type="G.1X" # ['Standard' | 'G.1X' | 'G.2X' | 'G.025x']
    )

    cdk.CfnOutput(self, f'{self.stack_name}_GlueJobName', value=glue_cfn_job.name)
    cdk.CfnOutput(self, f'{self.stack_name}_GlueJobRoleArn', value=glue_job_role.role_arn)
