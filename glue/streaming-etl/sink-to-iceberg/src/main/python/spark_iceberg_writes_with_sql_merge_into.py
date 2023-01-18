#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
import sys
import traceback

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue import DynamicFrame

from pyspark.context import SparkContext
from pyspark.conf import SparkConf
from pyspark.sql import DataFrame, Row
from pyspark.sql.window import Window
from pyspark.sql.functions import (
  col,
  desc,
  row_number,
  to_timestamp
)

args = getResolvedOptions(sys.argv, ['JOB_NAME',
  'catalog',
  'database_name',
  'table_name',
  'primary_key',
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
PRIMARY_KEY = args['primary_key']
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

def processBatch(data_frame, batch_id):
  if data_frame.count() > 0:
    stream_data_dynf = DynamicFrame.fromDF(
      data_frame, glueContext, "from_data_frame"
    )

    tables_df = spark.sql(f"SHOW TABLES IN {CATALOG}.{DATABASE}")
    table_list = tables_df.select('tableName').rdd.flatMap(lambda x: x).collect()
    if f"{TABLE_NAME}" not in table_list:
      print(f"Table {TABLE_NAME} doesn't exist in {CATALOG}.{DATABASE}.")
    else:
      _df = spark.sql(f"SELECT * FROM {CATALOG}.{DATABASE}.{TABLE_NAME} LIMIT 0")

      # Apply De-duplication logic on input data to pick up the latest record based on timestamp and operation
      window = Window.partitionBy(PRIMARY_KEY).orderBy(desc("m_time"))
      stream_data_df = stream_data_dynf.toDF()
      stream_data_df = stream_data_df.withColumn('m_time', to_timestamp(col('m_time'), 'yyyy-MM-dd HH:mm:ss'))
      upsert_data_df = stream_data_df.withColumn("row", row_number().over(window)) \
        .filter(col("row") == 1).drop("row") \
        .select(_df.schema.names)

      upsert_data_df.createOrReplaceTempView(f"{TABLE_NAME}_upsert")
      # print(f"Table '{TABLE_NAME}' is upserting...")

      try:
        spark.sql(f"""MERGE INTO {CATALOG}.{DATABASE}.{TABLE_NAME} t
          USING {TABLE_NAME}_upsert s ON s.{PRIMARY_KEY} = t.{PRIMARY_KEY}
          WHEN MATCHED THEN UPDATE SET *
          WHEN NOT MATCHED THEN INSERT *
          """)
      except Exception as ex:
        traceback.print_exc()
        raise ex

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
