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

class AuroraMysqlToS3Stack(Stack):

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

    s3_bucket_name = cdk.CfnParameter(self, 'TargetS3BucketName',
      type='String',
      description='DMS Target S3 Bucket name'
    )

    s3_bucket_folder_name = cdk.CfnParameter(self, 'TargetS3BucketFolderName',
      type='String',
      description='DMS Target S3 Bucket Folder name'
    )

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    # vpc_name = self.node.try_get_context('vpc_name')
    # vpc = aws_ec2.Vpc.from_lookup(self, 'DMSAuroraMysqlToS3VPC',
    #   is_default=True,
    #   vpc_name=vpc_name
    # )

    vpc = aws_ec2.Vpc(self, 'DMSAuroraMysqlToS3VPC',
      ip_addresses=aws_ec2.IpAddresses.cidr("10.0.0.0/16"),
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

    dms_vpc_role = aws_iam.Role(self, 'DMSVpcRole',
      role_name='dms-vpc-role',
      assumed_by=aws_iam.ServicePrincipal('dms.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonDMSVPCManagementRole'),
      ]
    )

    dms_cloudwatch_logs_role = aws_iam.Role(self, 'DMSCloudWatchLogsRole',
      role_name='dms-cloudwatch-logs-role',
      assumed_by=aws_iam.ServicePrincipal('dms.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonDMSCloudWatchLogsRole'),
      ]
    )

    dms_replication_subnet_group = aws_dms.CfnReplicationSubnetGroup(self, 'DMSReplicationSubnetGroup',
      replication_subnet_group_description='DMS Replication Subnet Group',
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
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
      replication_subnet_group_identifier=dms_replication_subnet_group.ref,
      vpc_security_group_ids=[db_client_sg.security_group_id]
    )

    #XXX: If you use `aws_cdk.SecretValue.unsafe_unwrap()` to get any secret value,
    # you may probably encounter ValueError; for example, invalid literal for int() with base 10: '${Token[TOKEN.228]}'
    # So you should need to make the API call in order to access a secret inside it.
    sm_client = boto3.client('secretsmanager', region_name=vpc.env.region)
    secret_name = self.node.try_get_context('aws_secret_name')
    secret_value = sm_client.get_secret_value(SecretId=secret_name)
    secret = json.loads(secret_value['SecretString'])

    source_endpoint_id = secret.get('dbClusterIdentifier', '').lower()
    dms_source_endpoint = aws_dms.CfnEndpoint(self, 'DMSSourceEndpoint',
      endpoint_identifier=source_endpoint_id,
      endpoint_type='source',
      engine_name=secret.get('engine', 'mysql'),
      server_name=secret.get('host'),
      port=int(secret.get('port', 3306)),
      database_name=secret.get('dbname'),
      username=secret.get('username'),
      password=secret.get('password')
    )

    dms_s3_access_role_policy_doc = aws_iam.PolicyDocument()
    dms_s3_access_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:PutObjectTagging",
        "s3:ListBucket"]
    }))

    dms_target_s3_access_role = aws_iam.Role(self, 'DMSTargetS3AccessRole',
      role_name='DMSTargetS3AccessRole',
      assumed_by=aws_iam.ServicePrincipal('dms.amazonaws.com'),
      inline_policies={
        'S3AccessRole': dms_s3_access_role_policy_doc
      }
    )

    target_endpoint_id = f"{source_endpoint_id}-to-s3"
    dms_target_endpoint = aws_dms.CfnEndpoint(self, 'DMSTargetEndpoint',
      endpoint_identifier=target_endpoint_id,
      endpoint_type='target',
      engine_name='s3',
      s3_settings=aws_dms.CfnEndpoint.S3SettingsProperty(
        bucket_name=s3_bucket_name.value_as_string,
        bucket_folder=s3_bucket_folder_name.value_as_string,
        service_access_role_arn=dms_target_s3_access_role.role_arn,
        data_format='parquet',
        parquet_timestamp_in_millisecond=True
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
        }
      ]
    }

    #XXX: AWS DMS - Using Amazon Kinesis Data Streams as a target for AWS Database Migration Service
    # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.Kinesis.html
    task_settings_json = {
      # Multithreaded full load task settings
      "FullLoadSettings": {
        "MaxFullLoadSubTasks": 8,
      }
    }

    dms_replication_task = aws_dms.CfnReplicationTask(self, 'DMSReplicationTask',
      replication_task_identifier='DMSMySQLToS3Task',
      replication_instance_arn=dms_replication_instance.ref,
      migration_type='full-load', # [ full-load | cdc | full-load-and-cdc ]
      source_endpoint_arn=dms_source_endpoint.ref,
      target_endpoint_arn=dms_target_endpoint.ref,
      table_mappings=json.dumps(table_mappings_json),
      replication_task_settings=json.dumps(task_settings_json)
    )


app = cdk.App()
AuroraMysqlToS3Stack(app, 'DMSAuroraMysqlToS3Stack', env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
