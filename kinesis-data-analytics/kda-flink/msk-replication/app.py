#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_kinesisanalytics as aws_kda_flink,
  aws_logs,
  aws_s3 as s3
)
from constructs import Construct


class MskReplicationStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    vpc_name = self.node.try_get_context('vpc_name')
    vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
      is_default=True,
      vpc_name=vpc_name)

    s3_bucket_name = self.node.try_get_context('s3_bucket_name')
    s3_bucket = s3.Bucket.from_bucket_name(self, 'S3KdaFlinkCodeLocation', s3_bucket_name)
    s3_path_to_flink_app_code = self.node.try_get_context('s3_path_to_flink_app_code')

    KDA_APP_NAME = 'KdaMskReplcation'

    kda_exec_role_policy_doc = aws_iam.PolicyDocument()
    kda_exec_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "ReadCode",
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["{}/{}".format(s3_bucket.bucket_arn, s3_path_to_flink_app_code)],
      "actions": ["s3:GetObject",
        "s3:GetObjectVersion"]
    }))

    kda_exec_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "ListCloudwatchLogGroups",
      "effect": aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [self.format_arn(service="logs", resource="log-group",
       resource_name="/aws/kinesis-analytics/{}:log-stream:*".format(KDA_APP_NAME),
       arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      "actions": ["logs:DescribeLogGroups"]
    }))

    kda_exec_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "ListCloudwatchLogStreams",
      "effect": aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [self.format_arn(service="logs", resource="log-group",
       resource_name="/aws/kinesis-analytics/{}:log-stream:kinesis-analytics-log-stream".format(KDA_APP_NAME),
       arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      "actions": ["logs:DescribeLogStreams"]
    }))

    kda_exec_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "PutCloudwatchLogs",
      "effect": aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [self.format_arn(service="logs", resource="log-group",
       resource_name="/aws/kinesis-analytics/{}:log-stream:kinesis-analytics-log-stream".format(KDA_APP_NAME),
       arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      "actions": ["logs:PutLogEvents"]
    }))

    kda_exec_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "ENIReadWritePermissions",
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "ec2:CreateNetworkInterface",
        "ec2:CreateNetworkInterfacePermission",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface"
      ]
    }))

    kda_exec_role_policy_name = "kinesis-analytics-service-{kda_app_name}-{region}".format(region=cdk.Aws.REGION,
      kda_app_name=KDA_APP_NAME),

    kda_execution_role = aws_iam.Role(self, 'KdaExecutionRole',
      role_name='kinesis-analytics-{kda_app_name}-{region}'.format(region=cdk.Aws.REGION,
        kda_app_name=KDA_APP_NAME),
      assumed_by=aws_iam.ServicePrincipal('kinesisanalytics.amazonaws.com'),
      path='/service-role/',
      inline_policies={
        'kinesis-analytics-service': kda_exec_role_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonVPCReadOnlyAccess'),
      ]
    )

    kda_flink_code_content = aws_kda_flink.CfnApplicationV2.CodeContentProperty(
      s3_content_location=aws_kda_flink.CfnApplicationV2.S3ContentLocationProperty(
        bucket_arn=s3_bucket.bucket_arn,
        file_key=s3_path_to_flink_app_code
      )
    )

    kda_flink_code_config = aws_kda_flink.CfnApplicationV2.ApplicationCodeConfigurationProperty(
      code_content=kda_flink_code_content,
      code_content_type='ZIPFILE'
    )

    kda_flink_property_groups = self.node.try_get_context('kda_flink_property_groups')
    _property_groups = [aws_kda_flink.CfnApplicationV2.PropertyGroupProperty(**elem)
      for elem in kda_flink_property_groups]
    kda_flink_env_props = aws_kda_flink.CfnApplicationV2.EnvironmentPropertiesProperty(
      property_groups = _property_groups
    )

    flink_app_config = aws_kda_flink.CfnApplicationV2.FlinkApplicationConfigurationProperty(
      checkpoint_configuration=aws_kda_flink.CfnApplicationV2.CheckpointConfigurationProperty(
        configuration_type='CUSTOM',
        checkpointing_enabled=True,
        checkpoint_interval=60000,
        min_pause_between_checkpoints=60000
      ),
      monitoring_configuration=aws_kda_flink.CfnApplicationV2.MonitoringConfigurationProperty(
        configuration_type='CUSTOM',
        log_level='INFO',
        metrics_level='TASK'
      ),
      parallelism_configuration=aws_kda_flink.CfnApplicationV2.ParallelismConfigurationProperty(
        configuration_type='CUSTOM',
        auto_scaling_enabled=False,
        parallelism=1,
        parallelism_per_kpu=1,
      )
    )

    kda_flink_app_config = aws_kda_flink.CfnApplicationV2.ApplicationConfigurationProperty(
      application_code_configuration=kda_flink_code_config,
      application_snapshot_configuration=aws_kda_flink.CfnApplicationV2.ApplicationSnapshotConfigurationProperty(
        snapshots_enabled=False
      ),
      environment_properties=kda_flink_env_props, 
      flink_application_configuration=flink_app_config
    )

    kda_app = aws_kda_flink.CfnApplicationV2(self, 'KdaMskReplication',
      runtime_environment='FLINK-1_11',
      service_execution_role=kda_execution_role.role_arn,
      application_configuration=kda_flink_app_config,
      application_description='A Kinesis Data Analytics application that reads from one Amazon MSK topic and writes to another',
      application_name=KDA_APP_NAME
    )

    kda_app_log_group = aws_logs.LogGroup(self, 'KdaMskReplicationLogGroup',
      log_group_name='/aws/kinesis-analytics/{}'.format(KDA_APP_NAME),
      retention=aws_logs.RetentionDays.THREE_DAYS,
      removal_policy=cdk.RemovalPolicy.DESTROY
    )

    kda_app_log_stream = aws_logs.LogStream(self, 'KdaMskReplicationLogStream',
      log_group=kda_app_log_group,
      log_stream_name='kinesis-analytics-log-stream',
      removal_policy=cdk.RemovalPolicy.DESTROY
    )

    #XXX: The ARN will be formatted as follows:
    # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
    kda_app_log_stream_arn = self.format_arn(service="logs", resource="log-group",
      resource_name="/aws/kinesis-analytics/{}:log-stream:kinesis-analytics-log-stream".format(KDA_APP_NAME),
      arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)

    kda_app_cw_log = aws_kda_flink.CfnApplicationCloudWatchLoggingOptionV2(self, 'KdaMskReplicationCWLog',
      application_name=kda_app.application_name,
      cloud_watch_logging_option=aws_kda_flink.CfnApplicationCloudWatchLoggingOptionV2.CloudWatchLoggingOptionProperty(log_stream_arn=kda_app_log_stream_arn)
    )
    kda_app_cw_log.add_dependency(kda_app)


app = cdk.App()
MskReplicationStack(app, "MskReplicationStack",
    env=cdk.Environment(
      account=os.getenv('CDK_DEFAULT_ACCOUNT'),
      region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
