#!/usr/bin/env python3
import os
import json

import boto3

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_dms,
  aws_iam,
)
from constructs import Construct

class AuroraMysqlToKinesisStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    database_name = cdk.CfnParameter(self, 'SourceDatabaseName',
      type='String',
      description='DMS Source Database name'
    )

    table_name = cdk.CfnParameter(self, 'SourceTableName',
      type='String',
      description='DMS Source Table name'
    )

    kinesis_stream_name = cdk.CfnParameter(self, 'TargetKinesisStreamName',
      type='String',
      description='DMS Target Kinesis Data Streams name'
    )

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    # vpc_name = self.node.try_get_context('vpc_name')
    # vpc = aws_ec2.Vpc.from_lookup(self, 'DMSAuroraMysqlToKinesisVPC',
    #   is_default=True,
    #   vpc_name=vpc_name
    # )

    vpc = aws_ec2.Vpc(self, 'DMSAuroraMysqlToKinesisVPC',
      ip_addresses=aws_ec2.IpAddresses.cidr("10.0.0.0/21"),
      max_azs=3,

      # 'subnetConfiguration' specifies the "subnet groups" to create.
      # Every subnet group will have a subnet for each AZ, so this
      # configuration will create `2 groups × 3 AZs = 6` subnets.
      subnet_configuration=[
        {
          "cidrMask": 24,
          "name": "Public",
          "subnetType": aws_ec2.SubnetType.PUBLIC,
        },
        {
          "cidrMask": 24,
          "name": "Private",
          "subnetType": aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
        }
      ],
      gateway_endpoints={
        "S3": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.S3
        )
      }
    )

    db_client_sg_name = self.node.try_get_context('mysql_client_security_group_name')
    db_client_sg = aws_ec2.SecurityGroup.from_lookup_by_name(self, 'MySQLClientSG', db_client_sg_name, vpc)

    dms_replication_subnet_group = aws_dms.CfnReplicationSubnetGroup(self, 'DMSReplicationSubnetGroup',
      replication_subnet_group_description='DMS Replication Subnet Group',
      subnet_ids=vpc.select_subnets().subnet_ids
    )

    dms_replication_instance = aws_dms.CfnReplicationInstance(self, 'DMSReplicationInstance',
      replication_instance_class='dms.t3.medium',
      # the properties below are optional
      allocated_storage=50,
      allow_major_version_upgrade=False,
      auto_minor_version_upgrade=False,
      engine_version='3.4.6',
      multi_az=False,
      preferred_maintenance_window='sat:03:17-sat:03:47',
      publicly_accessible=False,
      replication_subnet_group_identifier=dms_replication_subnet_group.replication_subnet_group_identifier,
      vpc_security_group_ids=[db_client_sg.security_group_id]
    )

    #XXX: If you use `aws_cdk.SecretValue.unsafe_unwrap()` to get any secret value,
    # you may probably encounter ValueError; for example, invalid literal for int() with base 10: '${Token[TOKEN.228]}'
    # So you should need to make the API call in order to access a secret inside it.
    sm_client = boto3.client('secretsmanager', region_name=vpc.env.region)
    secret_name = self.node.try_get_context('aws_secret_name')
    secret_value = sm_client.get_secret_value(SecretId=secret_name)
    secret = json.loads(secret_value['SecretString'])

    source_endpoint_id = secret['dbClusterIdentifier'].lower()
    dms_source_endpoint = aws_dms.CfnEndpoint(self, 'DMSSourceEndpoint',
      endpoint_identifier=source_endpoint_id,
      endpoint_type='source',
      engine_name=secret.get('engine'),
      server_name=secret.get('host'),
      port=int(secret.get('port')),
      database_name=secret.get('dbname'),
      username=secret.get('username'),
      password=secret.get('password')
    )

    dms_kinesis_access_role_policy_doc = aws_iam.PolicyDocument()
    dms_kinesis_access_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "kinesis:DescribeStream",
        "kinesis:PutRecord",
        "kinesis:PutRecords"]
    }))

    dms_target_kinesis_access_role = aws_iam.Role(self, 'DMSTargetKinesisAccessRole',
      role_name='DMSTargetKinesisAccessRole',
      assumed_by=aws_iam.ServicePrincipal('dms.amazonaws.com'),
      inline_policies={
        'KinesisAccessRole': dms_kinesis_access_role_policy_doc
      }
    )

    target_endpoint_id = f"{source_endpoint_id}-cdc-to-kinesis"
    dms_target_endpoint = aws_dms.CfnEndpoint(self, 'DMSTargetEndpoint',
      endpoint_identifier=target_endpoint_id,
      endpoint_type='target',
      engine_name='kinesis',
      kinesis_settings=aws_dms.CfnEndpoint.KinesisSettingsProperty(
        message_format="json-unformatted",
        service_access_role_arn=dms_target_kinesis_access_role.role_arn,
        # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
        stream_arn=self.format_arn(service='kinesis',
          region=cdk.Aws.REGION, account=cdk.Aws.ACCOUNT_ID,
          resource='stream', arn_format=cdk.ArnFormat.SLASH_RESOURCE_NAME,
          resource_name=kinesis_stream_name.value_as_string)
      )
    )

    table_mappings_json = {
      "rules": [
        {
          "rule-type": "selection",
          "rule-id": "1",
          "rule-name": "1",
          "object-locator": {
            "schema-name": database_name.value_as_string,
            "table-name": table_name.value_as_string
          },
          "rule-action": "include",
          "filters": []
        },
        {
          "rule-type": "object-mapping",
          "rule-id": "2",
          "rule-name": "DefaultMapToKinesis",
          "rule-action": "map-record-to-record",
          "object-locator": {
            "schema-name": database_name.value_as_string,
            "table-name": table_name.value_as_string
          }
        }
      ]
    }

    #XXX: AWS DMS - Using Amazon Kinesis Data Streams as a target for AWS Database Migration Service
    # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.Kinesis.html
    task_settings_json = {
      # Multithreaded full load task settings
      "FullLoadSettings": {
        "MaxFullLoadSubTasks": 8,
      },
      "TargetMetadata": {
        # Multithreaded full load task settings
        "ParallelLoadQueuesPerThread": 0,
        "ParallelLoadThreads": 0,
        "ParallelLoadBufferSize": 0,

        # Multithreaded CDC load task settings
        "ParallelApplyBufferSize": 1000,
        "ParallelApplyQueuesPerThread": 16,
        "ParallelApplyThreads": 8,
      }
    }

    dms_replication_task = aws_dms.CfnReplicationTask(self, 'DMSReplicationTask',
      replication_task_identifier='CDC-MySQLToKinesisTask',
      replication_instance_arn=dms_replication_instance.ref,
      migration_type='cdc', # [ full-load | cdc | full-load-and-cdc ]
      source_endpoint_arn=dms_source_endpoint.ref,
      target_endpoint_arn=dms_target_endpoint.ref,
      table_mappings=json.dumps(table_mappings_json),
      replication_task_settings=json.dumps(task_settings_json)
    )

    cdk.CfnOutput(self, 'DMSReplicationTaskId', value=dms_replication_task.replication_task_identifier)
    cdk.CfnOutput(self, 'DMSSourceEndpointId', value=dms_source_endpoint.endpoint_identifier)
    cdk.CfnOutput(self, 'DMSTargetEndpointId', value=dms_target_endpoint.endpoint_identifier)


app = cdk.App()
AuroraMysqlToKinesisStack(app, "AuroraMysqlToKinesisStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
