#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
import sys

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.conf import SparkConf
from pyspark.sql import DataFrame, Row
from awsglue import DynamicFrame


args = getResolvedOptions(sys.argv, ['JOB_NAME',
  'catalog',
  'database_name',
  'table_name',
  'kinesis_table_name',
  'kinesis_stream_arn',
  'starting_position_of_kinesis_iterator',
  'iceberg_s3_path',
  'lock_table_name',
  'aws_region',
  'window_size'
])

CATALOG = args['catalog']
ICEBERG_S3_PATH = args['iceberg_s3_path']
DATABASE = args['database_name']
TABLE_NAME = args['table_name']
DYNAMODB_LOCK_TABLE = args['lock_table_name']
KINESIS_STREAM_ARN = args['kinesis_stream_arn']
#XXX: starting_position_of_kinesis_iterator: ['LATEST', 'TRIM_HORIZON']
STARTING_POSITION_OF_KINESIS_ITERATOR = args.get('starting_position_of_kinesis_iterator', 'LATEST')
AWS_REGION = args['aws_region']
WINDOW_SIZE = args.get('window_size', '100 seconds')

def setSparkIcebergConf() -> SparkConf:
  conf_list = [
    (f"spark.sql.catalog.{CATALOG}", "org.apache.iceberg.spark.SparkCatalog"),
    (f"spark.sql.catalog.{CATALOG}.warehouse", ICEBERG_S3_PATH),
    (f"spark.sql.catalog.{CATALOG}.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog"),
    (f"spark.sql.catalog.{CATALOG}.io-impl", "org.apache.iceberg.aws.s3.S3FileIO"),
    (f"spark.sql.catalog.{CATALOG}.lock-impl", "org.apache.iceberg.aws.glue.DynamoLockManager"),
    (f"spark.sql.catalog.{CATALOG}.lock.table", DYNAMODB_LOCK_TABLE),
    ("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"),
    ("spark.sql.iceberg.handle-timestamp-without-timezone", "true")
  ]
  spark_conf = SparkConf().setAll(conf_list)
  return spark_conf

# Set the Spark + Glue context
conf = setSparkIcebergConf()
sc = SparkContext(conf=conf)
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

kds_df = glueContext.create_data_frame.from_options(
  connection_type="kinesis",
  connection_options={
    "typeOfData": "kinesis",
    "streamARN": KINESIS_STREAM_ARN,
    "classification": "json",
    "startingPosition": f"{STARTING_POSITION_OF_KINESIS_ITERATOR}",
    "inferSchema": "true",
  },
  transformation_ctx="kds_df",
)

def sparkSqlQuery(glueContext, query, mapping, transformation_ctx) -> DynamicFrame:
  for alias, frame in mapping.items():
    frame.toDF().createOrReplaceTempView(alias)
  result = spark.sql(query)
  return DynamicFrame.fromDF(result, glueContext, transformation_ctx)

def processBatch(data_frame, batch_id):
  if data_frame.count() > 0:
    stream_data_df = DynamicFrame.fromDF(
      data_frame, glueContext, "from_data_frame"
    )

    sql_query = f"""
    INSERT INTO {CATALOG}.{DATABASE}.{TABLE_NAME} SELECT myDataSource.name, myDataSource.age FROM myDataSource;
    """
    insert_into_icebeg_table = sparkSqlQuery(
      glueContext,
      query=sql_query,
      mapping={"myDataSource": stream_data_df},
      transformation_ctx="insert_into_icebeg_table",
    )

checkpointPath = os.path.join(args["TempDir"], args["JOB_NAME"], "checkpoint/")

glueContext.forEachBatch(
  frame=kds_df,
  batch_function=processBatch,
  options={
    "windowSize": WINDOW_SIZE,
    "checkpointLocation": checkpointPath,
  }
)

job.commit()
