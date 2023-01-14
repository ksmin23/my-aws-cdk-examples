#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
import sys
import datetime

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue import DynamicFrame

from pyspark.conf import SparkConf
from pyspark.sql import DataFrame, Row
from pyspark.sql.types import *
from pyspark.sql.functions import *

args = getResolvedOptions(sys.argv, ['JOB_NAME',
  'catalog',
  'database_name',
  'table_name',
  'kinesis_table_name',
  'kinesis_stream_name',
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
KINESIS_STREAM_NAME = args['kinesis_stream_name']
#XXX: starting_position_of_kinesis_iterator: ['LATEST', 'TRIM_HORIZON']
STARTING_POSITION_OF_KINESIS_ITERATOR = args.get('starting_position_of_kinesis_iterator', 'LATEST')
AWS_REGION = args['aws_region']
WINDOW_SIZE = args.get('window_size', '100 seconds')

def set_spark_iceberg_conf() -> SparkConf:
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
conf = set_spark_iceberg_conf()
sc = SparkContext(conf=conf)
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read from Kinesis Data Stream
streaming_data = spark.readStream \
                    .format("kinesis") \
                    .option("streamName", KINESIS_STREAM_NAME) \
                    .option("endpointUrl", f"https://kinesis.{AWS_REGION}.amazonaws.com") \
                    .option("startingPosition", STARTING_POSITION_OF_KINESIS_ITERATOR) \
                    .load()

checkpointPath = os.path.join(args["TempDir"], args["JOB_NAME"], "checkpoint/")
streaming_data.printSchema()

table_identifier = f"{CATALOG}.{DATABASE}.{TABLE_NAME}"

dataDF = streaming_data \
    .select(from_json(col("data") \
    .cast("string"), glueContext.get_catalog_schema_as_spark_schema(DATABASE, TABLE_NAME)) \
    .alias("source_table")) \
    .select("source_table.*")

dataDF.printSchema()

query = dataDF.writeStream \
    .format("iceberg") \
    .outputMode("append") \
    .trigger(processingTime=WINDOW_SIZE) \
    .option("path", table_identifier) \
    .option("fanout-enabled", "true") \
    .option("checkpointLocation", checkpointPath) \
    .start()

query.awaitTermination()
