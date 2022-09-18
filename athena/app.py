#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_athena,
  aws_s3 as s3,
)
from constructs import Construct

random.seed(31)

class AthenaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    ATHENA_WORK_GROUP_NAME = cdk.CfnParameter(self, 'AthenaWorkGroupName',
      type='String',
      description='Amazon Athena Workgroup Name',
      default='dev'
    )

    S3_BUCKET_SUFFIX = ''.join(random.sample((string.ascii_lowercase + string.digits), k=7))
    s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: core.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name='aws-athena-query-results-{region}-{suffix}'.format(
        region=cdk.Aws.REGION, suffix=S3_BUCKET_SUFFIX))

    athena_cfn_work_group = aws_athena.CfnWorkGroup(self, 'AthenaCfnWorkGroup',
      name='dev',

      # the properties below are optional
      description='workgroup for developer',
      recursive_delete_option=False,
      state='ENABLED', # [DISABLED, ENABLED]
      tags=[cdk.CfnTag(
        key='Name',
        value=ATHENA_WORK_GROUP_NAME.value_as_string
      )],
      work_group_configuration=aws_athena.CfnWorkGroup.WorkGroupConfigurationProperty(
        # bytes_scanned_cutoff_per_query=11000000,
        #XXX: EnforceWorkGroupConfiguration
        # Link: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-athena-workgroup-workgroupconfiguration.html#cfn-athena-workgroup-workgroupconfiguration-enforceworkgroupconfiguration
        # If set to "true", the settings for the workgroup override client-side settings.
        # If set to "false", client-side settings are used.
        enforce_work_group_configuration=False,
        engine_version=aws_athena.CfnWorkGroup.EngineVersionProperty(
          effective_engine_version='Athena engine version 2',
          selected_engine_version='Athena engine version 2'
        ),
        publish_cloud_watch_metrics_enabled=True,
        requester_pays_enabled=True,
        result_configuration=aws_athena.CfnWorkGroup.ResultConfigurationProperty(
          output_location=s3_bucket.s3_url_for_object()
        )
      )
    )

    query = '''/* Create your database */
CREATE DATABASE IF NOT EXISTS mydatabase;

/* Create table with partitions */
CREATE EXTERNAL TABLE `mydatabase.web_log_json`(
  `userId` string,
  `sessionId` string,
  `referrer` string,
  `userAgent` string,
  `ip` string,
  `hostname` string,
  `os` string,
  `timestamp` timestamp,
  `uri` string)
PARTITIONED BY (
  `year` int,
  `month` int,
  `day` int,
  `hour` int)
ROW FORMAT SERDE
  'org.openx.data.jsonserde.JsonSerDe'
STORED AS INPUTFORMAT
  'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.IgnoreKeyTextOutputFormat'
LOCATION
  's3://bucket-name/folder';

/* Next we will load the partitions for this table */
MSCK REPAIR TABLE mydatabase.web_log_json;

/* Check the partitions */
SHOW PARTITIONS mydatabase.web_log_json;

SELECT COUNT(*) FROM mydatabase.web_log_json;
'''

    athena_cfn_named_query = aws_athena.CfnNamedQuery(self, "MyAthenaCfnNamedQuery1",
      database="default",
      query_string=query,

      # the properties below are optional
      description="Sample Hive DDL statement to create a partitioned table pointing to web log data (json)",
      name="Create Web Log table (json) with partitions",
      work_group=athena_cfn_work_group.name
    )    

    query = '''/* Create your database */
CREATE DATABASE IF NOT EXISTS mydatabase;

/* Create table with partitions */
CREATE EXTERNAL TABLE `mydatabase.web_log_parquet`(
  `userId` string,
  `sessionId` string,
  `referrer` string,
  `userAgent` string,
  `ip` string,
  `hostname` string,
  `os` string,
  `timestamp` timestamp,
  `uri` string)
PARTITIONED BY (
  `year` int,
  `month` int,
  `day` int,
  `hour` int)
ROW FORMAT SERDE
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://bucket-name/folder';

/* Next we will load the partitions for this table */
MSCK REPAIR TABLE mydatabase.web_log_parquet;

/* Check the partitions */
SHOW PARTITIONS mydatabase.web_log_parquet;

SELECT COUNT(*) FROM mydatabase.web_log_parquet;
'''

    athena_cfn_named_query = aws_athena.CfnNamedQuery(self, "MyAthenaCfnNamedQuery2",
      database="default",
      query_string=query,

      # the properties below are optional
      description="Sample Hive DDL statement to create a partitioned table pointing to web log data (parquet)",
      name="Create Web Log table (parquet) with partitions",
      work_group=athena_cfn_work_group.name
    )

    cdk.CfnOutput(self, 'f{self.stack_name}_AthenaWorkGroupName', value=athena_cfn_work_group.name,
      export_name='AthenaWorkGroupName')


app = cdk.App()
AthenaStack(app, "AthenaStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
