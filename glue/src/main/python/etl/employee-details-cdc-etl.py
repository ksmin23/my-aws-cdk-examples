#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
from datetime import datetime

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

from pyspark.conf import SparkConf
from pyspark.sql.window import Window
from pyspark.sql.functions import (
  concat,
  col,
  lit,
  max,
  rank,
  to_timestamp
)

# Define Glue job arguments from Glue job parameters
args = getResolvedOptions(sys.argv, ['JOB_NAME',
  'raw_s3_path',
  'iceberg_s3_path',
  'catalog',
  'database',
  'table_name',
  'primary_key',
  'partition_key',
  'lock_table_name'])

# Examples of Glue Job Parameters
# raw_s3_path : s3://aws-glue-input-parquet-atq4q5u/cdc-load/
# iceberg_s3_path : s3://aws-glue-output-iceberg-atq4q5u
# catalog : job_catalog
# database : human_resources
# table_name : employee_details_iceberg
# primary_key : emp_no
# partition_key : department
# lock_table_name : employee_details_lock

# Set variables
RAW_S3_PATH = args.get("raw_s3_path")
CATALOG = args.get("catalog")
ICEBERG_S3_PATH = args.get("iceberg_s3_path")
DATABASE = args.get("database")
TABLE_NAME = args.get("table_name")
PK = args.get("primary_key")
PARTITION = args.get("partition_key")
DYNAMODB_LOCK_TABLE = args.get("lock_table_name")

# Set the Spark Configuration of Apache Iceberg. You can refer the Apache Iceberg Connector Usage Instructions.
def set_spark_iceberg_conf() -> SparkConf:
  conf = SparkConf()

  conf.set(f"spark.sql.catalog.{CATALOG}", "org.apache.iceberg.spark.SparkCatalog")
  conf.set(f"spark.sql.catalog.{CATALOG}.warehouse", ICEBERG_S3_PATH)
  conf.set(f"spark.sql.catalog.{CATALOG}.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
  conf.set(f"spark.sql.catalog.{CATALOG}.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
  conf.set(f"spark.sql.catalog.{CATALOG}.lock-impl", "org.apache.iceberg.aws.glue.DynamoLockManager")
  conf.set(f"spark.sql.catalog.{CATALOG}.lock.table", DYNAMODB_LOCK_TABLE)
  conf.set("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
  conf.set("spark.sql.iceberg.handle-timestamp-without-timezone","true")

  return conf

# Set the Spark + Glue context
conf = set_spark_iceberg_conf()
glueContext = GlueContext(SparkContext(conf=conf))
spark = glueContext.spark_session

job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read data from S3 location where is cdc-loaded by DMS
cdcDynamicFrame = glueContext.create_dynamic_frame_from_options(
  connection_type='s3',
  connection_options={
    'paths': [f'{RAW_S3_PATH}'],
    'groupFiles': 'none',
    'recurse': True
  },
  format='parquet',
  transformation_ctx='cdcDyf')

print(f"Count of CDC data after last job bookmark:{cdcDynamicFrame.count()}")

if cdcDynamicFrame.count() == 0:
  print(f"No Data changed.")
else:
  cdcDF = cdcDynamicFrame.toDF()
  cdcDF = cdcDF.withColumn('m_time', to_timestamp(col('m_time')))

  # Apply De-duplication logic on input data, to pickup latest record based on timestamp and operation
  # For example, emp_no is unique key
  IDWindowDF = Window.partitionBy(cdcDF.emp_no).orderBy(cdcDF.m_time).rangeBetween(-sys.maxsize, sys.maxsize)

  # Add new columns to capture first and last OP value and what is the latest timestamp
  inputDFWithTS = cdcDF.withColumn("max_op_date", max(cdcDF.m_time).over(IDWindowDF))

  # Filter out new records that are inserted, then select latest record from existing records and merge both to get deduplicated output 
  newInsertedDF = inputDFWithTS.filter("m_time=max_op_date").filter("Op='I'")
  updatedOrDeletedDF = inputDFWithTS.filter("m_time=max_op_date").filter("Op IN ('U', 'D')")
  finalInputDF = newInsertedDF.unionAll(updatedOrDeletedDF)

  CURRENT_DATETIME = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  finalInputDF = finalInputDF.withColumn('last_applied_date', to_timestamp(lit(CURRENT_DATETIME)))

  cdcInsertCount = finalInputDF.filter("Op = 'I'").count()
  cdcUpdateCount = finalInputDF.filter("Op = 'U'").count()
  cdcDeleteCount = finalInputDF.filter("Op = 'D'").count()
  totalCDCCount = finalInputDF.count()
  print(f"Inserted count:  {cdcInsertCount}")
  print(f"Updated count:   {cdcUpdateCount}")
  print(f"Deleted count:   {cdcDeleteCount}")
  print(f"Total CDC count: {totalCDCCount}")

  # Merge CDC data into Iceberg Table
  dropColumnList = ['Op', 'schema_name', 'table_name', 'max_op_date']

  tablesDF = spark.sql(f"SHOW TABLES IN {CATALOG}.{DATABASE}")
  table_list = tablesDF.select('tableName').rdd.flatMap(lambda x: x).collect()
  if f"{TABLE_NAME}" not in table_list:
    print(f"Table {TABLE_NAME} doesn't exist in {CATALOG}.{DATABASE}.")
  else:
    # DataFrame for the inserted or updated data
    upsertedDF = finalInputDF.filter("Op != 'D'").drop(*dropColumnList)
    if upsertedDF.count() > 0:
      upsertedDF.createOrReplaceTempView(f"{TABLE_NAME}_upsert")
      print(f"Table {TABLE_NAME} is upserting...")
      spark.sql(f"""MERGE INTO {CATALOG}.{DATABASE}.{TABLE_NAME} t
        USING {TABLE_NAME}_upsert s ON s.{PK} = t.{PK}
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """)
    else:
      print("No data to insert or update.")

    # DataFrame for the deleted data
    deletedDF = finalInputDF.filter("Op = 'D'").drop(*dropColumnList)
    if deletedDF.count() > 0:
      deletedDF.createOrReplaceTempView(f"{TABLE_NAME}_delete")
      print(f"Table {TABLE_NAME} is deleting...")
      spark.sql(f"""MERGE INTO {CATALOG}.{DATABASE}.{TABLE_NAME} t
        USING {TABLE_NAME}_delete s ON s.{PK} = t.{PK}
        WHEN MATCHED THEN DELETE
        """)
    else:
      print("No data to delete.")

    # Read data from Apache Iceberg Table
    spark.sql(f"SELECT * FROM {CATALOG}.{DATABASE}.{TABLE_NAME} limit 5").show()
    print(f"Total count of {TABLE_NAME} Table Results:\n")
    countDF = spark.sql(f"SELECT count(*) FROM {CATALOG}.{DATABASE}.{TABLE_NAME}")
    print(f"{countDF.show()}")
    print(f"Iceberg data load is completed successfully.")

job.commit()
print(f"Glue Job is completed successfully.")
