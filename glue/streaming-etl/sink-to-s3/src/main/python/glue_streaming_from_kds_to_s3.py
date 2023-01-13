#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
import sys
import datetime

from pyspark.sql import DataFrame, Row
from pyspark.context import SparkContext
from pyspark.sql.types import *
from pyspark.sql.functions import *

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue import DynamicFrame


args = getResolvedOptions(sys.argv, [
  'JOB_NAME',
  'aws_region',
  'output_path',
  'glue_database',
  'glue_table_name',
  'stream_starting_position'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

stream_starting_position = args.get('stream_starting_position', 'TRIM_HORIZON')
database = args['glue_database']
table_name = args['glue_table_name']

aws_region = args['aws_region']
output_path = args['output_path']

s3_target = os.path.join(output_path, "ventilator_metrics")
checkpoint_location = os.path.join(output_path, "cp/")
temp_path = os.path.join(output_path, "temp/")

def processBatch(data_frame, batchId):
  _now = datetime.datetime.now()

  year, month, day, hour = (_now.year, _now.month, _now.day, _now.hour)
  partition = f"/ingest_year={year:0>4}/ingest_month={month:0>2}/ingest_day={day:0>2}/ingest_hour={hour:0>2}/"

  if (data_frame.count() > 0):
    dynamic_frame = DynamicFrame.fromDF(data_frame, glueContext, "from_data_frame")
    apply_mapping = ApplyMapping.apply(frame=dynamic_frame, mappings = [
      ("ventilatorid", "long", "ventilatorid", "long"),
      ("eventtime", "string", "eventtime", "timestamp"),
      ("serialnumber", "string", "serialnumber", "string"),
      ("pressurecontrol", "long", "pressurecontrol", "long"),
      ("o2stats", "long", "o2stats", "long"),
      ("minutevolume", "long", "minutevolume", "long"),
      ("manufacturer", "string", "manufacturer", "string")],
      transformation_ctx = "apply_mapping")

    # Write to S3 Sink
    s3path = s3_target + partition
    s3sink = glueContext.write_dynamic_frame.from_options(frame=apply_mapping, connection_type="s3",
      connection_options={"path": s3path}, format="parquet", transformation_ctx="s3sink")

# Read from Kinesis Data Stream
sourceData = glueContext.create_data_frame.from_catalog(
  database = database,
  table_name = table_name,
  transformation_ctx = "datasource1",
  additional_options = {"startingPosition": stream_starting_position, "inferSchema": "true"})

glueContext.forEachBatch(frame=sourceData,
  batch_function=processBatch,
  options = {
    "windowSize": "100 seconds",
    "checkpointLocation": checkpoint_location
  })

job.commit()
