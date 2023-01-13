#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue import DynamicFrame

from pyspark.sql.session import SparkSession
from pyspark.sql import DataFrame, Row
from pyspark.sql.functions import * 
from pyspark.sql.functions import col, to_timestamp, monotonically_increasing_id, to_date, when


## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ["JOB_NAME",
  "database_name",
  "kinesis_table_name",
  "starting_position_of_kinesis_iterator",
  "hudi_table_name",
  "window_size",
  "s3_path_hudi",
  "spark_checkpoint_s3_path"])

spark = SparkSession.builder.config('spark.serializer', 'org.apache.spark.serializer.KryoSerializer').config('spark.sql.hive.convertMetastoreParquet', 'false').getOrCreate()

sc = spark.sparkContext
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

database_name = args["database_name"]
kinesis_table_name = args["kinesis_table_name"]
hudi_table_name = args["hudi_table_name"]
s3_path_hudi = args["s3_path_hudi"]
s3_path_to_checkpoint = args["spark_checkpoint_s3_path"]

# can be set to "LATEST", "TRIM_HORIZON" or "EARLIEST"
starting_position_of_kinesis_iterator = args["starting_position_of_kinesis_iterator"]

# The amount of time to spend processing each batch
window_size = args["window_size"]

data_frame_DataSource0 = glueContext.create_data_frame.from_catalog(
  database = database_name,
  table_name = kinesis_table_name,
  transformation_ctx = "DataSource0",
  additional_options = {"inferSchema":"true", "startingPosition": starting_position_of_kinesis_iterator}
)

# config
commonConfig = {
  'path': s3_path_hudi
}

hudiWriteConfig = {
  'className' : 'org.apache.hudi',
  'hoodie.table.name': hudi_table_name,
  'hoodie.datasource.write.operation': 'upsert',
  'hoodie.datasource.write.table.type': 'COPY_ON_WRITE',
  'hoodie.datasource.write.precombine.field': 'date',
  'hoodie.datasource.write.recordkey.field': 'name',
  'hoodie.datasource.write.partitionpath.field': 'name:SIMPLE,year:SIMPLE,month:SIMPLE,day:SIMPLE',
  'hoodie.datasource.write.keygenerator.class': 'org.apache.hudi.keygen.CustomKeyGenerator',
  'hoodie.deltastreamer.keygen.timebased.timestamp.type': 'MIXED',
  'hoodie.deltastreamer.keygen.timebased.input.dateformat': 'yyyy-mm-dd',
  'hoodie.deltastreamer.keygen.timebased.output.dateformat':'yyyy/MM/dd'
}

hudiGlueConfig = {
  'hoodie.datasource.hive_sync.enable': 'true',
  'hoodie.datasource.hive_sync.sync_as_datasource': 'false',
  'hoodie.datasource.hive_sync.database': database_name,
  'hoodie.datasource.hive_sync.table': hudi_table_name,
  'hoodie.datasource.hive_sync.use_jdbc':'false',
  'hoodie.datasource.write.hive_style_partitioning' : 'true',
  'hoodie.datasource.hive_sync.partition_extractor_class': 'org.apache.hudi.hive.MultiPartKeysValueExtractor',
  'hoodie.datasource.hive_sync.partition_fields': 'name,year,month,day'
}

combinedConf = {
  **commonConfig,
  **hudiWriteConfig,
  **hudiGlueConfig
}

# ensure the incomong record has the correct current schema, new fresh columns are fine, if a column exists in current schema but not in incoming record then manually add before inserting
def evolveSchema(kinesis_df, table, forcecast=False):
  try:
    #get existing table's schema
    glue_catalog_df = spark.sql(f"SELECT * FROM {table} LIMIT 0")

    #sanitize for hudi specific system columns
    columns_to_drop = ['_hoodie_commit_time', '_hoodie_commit_seqno', '_hoodie_record_key', '_hoodie_partition_path', '_hoodie_file_name']
    glue_catalog_df_sanitized = glue_catalog_df.drop(*columns_to_drop)
    if (kinesis_df.schema != glue_catalog_df_sanitized.schema):
      merged_df = kinesis_df.unionByName(glue_catalog_df_sanitized, allowMissingColumns=True)
    return merged_df
  except Exception as e:
    print(e)
    return kinesis_df

def processBatch(data_frame, batch_id):
  
  if data_frame.count() > 0:

    kinesis_dynamic_frame = DynamicFrame.fromDF(data_frame, glueContext, "from_kinesis_data_frame")
    kinesis_data_frame = kinesis_dynamic_frame.toDF()

    kinesis_data_frame = evolveSchema(kinesis_data_frame, f"{database_name}.{hudi_table_name}", False)

    glueContext.write_dynamic_frame.from_options(
      frame = DynamicFrame.fromDF(kinesis_data_frame, glueContext, "evolved_kinesis_data_frame"),
      connection_type = "custom.spark",
      connection_options = combinedConf
    )

glueContext.forEachBatch(
  frame = data_frame_DataSource0,
  batch_function = processBatch,
  options = {
    "windowSize": window_size,
    "checkpointLocation": s3_path_to_checkpoint
  }
)

job.commit()
