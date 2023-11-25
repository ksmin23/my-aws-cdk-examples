#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_s3 as s3,
  aws_mwaa as mwaa
)
from constructs import Construct

random.seed(47)


class MwaaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    s3_bucket_name = self.node.try_get_context('s3_bucket_for_dag_code')
    s3_bucket = s3.Bucket.from_bucket_name(self, "S3BucketForDAGCode", s3_bucket_name)

    DEFAULT_MWAA_ENV_NAME = 'MyAirflowEnv-{}'.format(''.join(random.sample((string.ascii_letters), k=5)))
    MY_MWAA_ENV_NAME = self.node.try_get_context('airflow_env_name')
    MY_MWAA_ENV_NAME = MY_MWAA_ENV_NAME if MY_MWAA_ENV_NAME else DEFAULT_MWAA_ENV_NAME

    sg_mwaa = aws_ec2.SecurityGroup(self, "AirflowSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon MWAA Environment {}'.format(MY_MWAA_ENV_NAME),
      security_group_name='airflow-sg-{}'.format(MY_MWAA_ENV_NAME)
    )
    sg_mwaa.add_ingress_rule(peer=sg_mwaa, connection=aws_ec2.Port.all_traffic(), description='airflow security group')
    cdk.Tags.of(sg_mwaa).add('Name', 'airflow-sg-{}'.format(MY_MWAA_ENV_NAME))

    mwaa_execution_policy_doc = aws_iam.PolicyDocument()
    mwaa_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [self.format_arn(service="airflow", resource="environment",
        resource_name=MY_MWAA_ENV_NAME, arn_format=cdk.ArnFormat.SLASH_RESOURCE_NAME)],
      "actions": ["airflow:PublishMetrics"]
    }))

    mwaa_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.DENY,
      "resources": [s3_bucket.bucket_arn,
        "{}/*".format(s3_bucket.bucket_arn)],
      "actions": ["s3:ListAllMyBuckets"]
    }))

    mwaa_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [s3_bucket.bucket_arn,
        "{}/*".format(s3_bucket.bucket_arn)],
      "actions": ["s3:GetObject*",
        "s3:GetBucket*",
        "s3:List*"]
    }))

    mwaa_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [self.format_arn(service="logs", resource="log-group",
        resource_name="airflow-{}-*".format(MY_MWAA_ENV_NAME), arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      "actions": ["logs:CreateLogStream",
        "logs:CreateLogGroup",
        "logs:PutLogEvents",
        "logs:GetLogEvents",
        "logs:GetLogRecord",
        "logs:GetLogGroupFields",
        "logs:GetQueryResults"]
    }))

    mwaa_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": ["logs:DescribeLogGroups"]
    }))

    mwaa_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": ["cloudwatch:PutMetricData"]
    }))

    mwaa_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [self.format_arn(service="sqs", account="*", resource="airflow-celery-*")],
      "actions": ["sqs:ChangeMessageVisibility",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:GetQueueUrl",
        "sqs:ReceiveMessage",
        "sqs:SendMessage"]
    }))

    mwaa_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "actions": ["kms:Decrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey*",
        "kms:Encrypt"],
      "not_resources": [self.format_arn(service="kms", region="*", resource="key",
        resource_name="*", arn_format=cdk.ArnFormat.SLASH_RESOURCE_NAME)],
      "conditions": {
        "StringLike": {
          "kms:ViaService": [
            "sqs.{region}.amazonaws.com".format(region=kwargs['env'].region)
          ]
        }
      }
    }))

    mwaa_execution_role = aws_iam.Role(self, 'MWAAExecutionRole',
      role_name='AmazonMWAA-{name}-{suffix}'.format(name=MY_MWAA_ENV_NAME, suffix=str(kwargs['env'].account)[-5:]),
      assumed_by=aws_iam.ServicePrincipal('airflow.amazonaws.com'),
      path='/service-role/',
      inline_policies={
        'MWAA-Execution-Policy': mwaa_execution_policy_doc
      }
    )

    #XXX: https://github.com/aws/aws-cdk/issues/3227
    mwaa_execution_role.assume_role_policy.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "actions": ["sts:AssumeRole"],
      "principals": [
        aws_iam.ServicePrincipal('airflow-env.amazonaws.com')
      ]
    }))

    #XXX: NetworkConfiguration.SubnetIds: expected maximum item count: 2
    MAX_SUBNET_IDS = 2
    mwaa_network_conf= mwaa.CfnEnvironment.NetworkConfigurationProperty(
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids[:MAX_SUBNET_IDS],
      security_group_ids=[sg_mwaa.security_group_id]
    )

    mwaa_logging_conf = mwaa.CfnEnvironment.LoggingConfigurationProperty(
      dag_processing_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(enabled=True, log_level="WARNING"),
      scheduler_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(enabled=True, log_level="WARNING"),
      task_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(enabled=True, log_level="INFO"),
      webserver_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(enabled=True, log_level="WARNING"),
      worker_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(enabled=True, log_level="WARNING")
    )

    mwaa_conf_options = {
      "logging.logging_level": "INFO",
      "core.default_timezone": "utc"
    }

    airflow_env = mwaa.CfnEnvironment(self, "MyAirflow",
      name=MY_MWAA_ENV_NAME,
      airflow_configuration_options=mwaa_conf_options,
      airflow_version="2.0.2", #XXX: Valid values=[2.0.2, 1.10.12]
      dag_s3_path="dags",
      environment_class="mw1.small", #XXX: Valid values=[mw1.small, mw1.medium, mw1.large]
      execution_role_arn= mwaa_execution_role.role_arn,
      logging_configuration=mwaa_logging_conf,
      max_workers=2,
      min_workers=1,
      network_configuration=mwaa_network_conf,
      requirements_s3_path="requirements/requirements.txt",
      source_bucket_arn=s3_bucket.bucket_arn,
      #tags={"env": "staging", "service": "airflow"}, #XXX: https://github.com/aws/aws-cdk/issues/13772
      webserver_access_mode="PUBLIC_ONLY",
      weekly_maintenance_window_start="SUN:03:30"
    )


    cdk.CfnOutput(self, 'AirflowEnvName', value=airflow_env.name, export_name=f'{self.stack_name}-AirflowEnvName')
    cdk.CfnOutput(self, 'AirflowVersion', value=airflow_env.airflow_version, export_name=f'{self.stack_name}-AirflowVersion')
    cdk.CfnOutput(self, 'AirflowSourceBucketArn', value=airflow_env.source_bucket_arn, export_name=f'{self.stack_name}-AirflowSourceBucketArn')
    cdk.CfnOutput(self, 'AirflowDagS3Path', value=airflow_env.dag_s3_path, export_name=f'{self.stack_name}-AirflowDagS3Path')
    cdk.CfnOutput(self, 'MWAAEnvironmentClass', value=airflow_env.environment_class, export_name=f'{self.stack_name}-MWAAEnvironmentClass')
    cdk.CfnOutput(self, 'MWAASecurityGroupID', value=sg_mwaa.security_group_id, export_name=f'{self.stack_name}-MWAASecurityGroupID')
    cdk.CfnOutput(self, 'MWAAExecutionRoleArn', value=airflow_env.execution_role_arn, export_name=f'{self.stack_name}-MWAAExecutionRoleArn')
