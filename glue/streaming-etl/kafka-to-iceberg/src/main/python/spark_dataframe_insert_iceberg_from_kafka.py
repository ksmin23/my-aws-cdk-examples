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
from awsglue import DynamicFrame

from pyspark.conf import SparkConf
from pyspark.sql.types import *
from pyspark.sql.functions import (
  col,
  from_json,
  to_timestamp
)


args = getResolvedOptions(sys.argv, ['JOB_NAME',
  'catalog',
  'database_name',
  'table_name',
  'primary_key',
  'kafka_topic_name',
  'starting_offsets_of_kafka_topic',
  'kafka_connection_name',
  'kafka_bootstrap_servers',
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

KAFKA_TOPIC_NAME = args['kafka_topic_name']
KAFKA_CONNECTION_NAME = args['kafka_connection_name']
KAFKA_BOOTSTRAP_SERVERS = args['kafka_bootstrap_servers']

#XXX: starting_offsets_of_kafka_topic: ['latest', 'earliest']
STARTING_OFFSETS_OF_KAFKA_TOPIC = args.get('starting_offsets_of_kafka_topic', 'latest')

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

options_read = {
  # "kafka.bootstrap.servers": "b-1.icebergdemostream.khxj9u.c3.kafka.us-east-1.amazonaws.com:9092,b-2.icebergdemostream.khxj9u.c3.kafka.us-east-1.amazonaws.com:9092,b-3.icebergdemostream.khxj9u.c3.kafka.us-east-1.amazonaws.com:9092",
  "kafka.bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
  "subscribe": KAFKA_TOPIC_NAME,
  "startingOffsets": STARTING_OFFSETS_OF_KAFKA_TOPIC
}

schema = StructType([
  StructField("name", StringType(), False),
  StructField("age", IntegerType(), True),
  StructField("m_time", StringType(), False),
])

streaming_data = spark.readStream.format("kafka").options(**options_read).load()

stream_data_df = streaming_data \
    .select(from_json(col("value").cast("string"), schema).alias("source_table")) \
    .select("source_table.*") \
    .withColumn('m_time', to_timestamp(col('m_time'), 'yyyy-MM-dd HH:mm:ss'))

table_id = f"{CATALOG}.{DATABASE}.{TABLE_NAME}"
checkpointPath = os.path.join(args["TempDir"], args["JOB_NAME"], "checkpoint/")

#XXX: Writing against partitioned table
# https://iceberg.apache.org/docs/0.14.0/spark-structured-streaming/#writing-against-partitioned-table
# Complete output mode not supported when there are no streaming aggregations on streaming DataFrame/Datasets
query = stream_data_df.writeStream \
    .format("iceberg") \
    .outputMode("append") \
    .trigger(processingTime=WINDOW_SIZE) \
    .option("path", table_id) \
    .option("fanout-enabled", "true") \
    .option("checkpointLocation", checkpointPath) \
    .start()

query.awaitTermination()
