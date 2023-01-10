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

GLUE_DATABASE = args['glue_database']
GLUE_TABLE_NAME = args['glue_table_name']
STREAM_STARTING_POSITION = args.get('stream_starting_position', 'LATEST')

# S3 sink locations
AWS_REGION = args['aws_region']
OUTPUT_PATH = args['output_path']

S3_TARGET = os.path.join(OUTPUT_PATH, "ventilator_metrics")
CHECKPOINT_LOCATION = os.path.join(OUTPUT_PATH, "cp/")
TEMP_PATH = os.path.join(OUTPUT_PATH, "temp/")

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

        # dynamic_frame.printSchema()

        # Write to S3 Sink
        s3path = os.path.join(S3_TARGET, partition)
        _s3sink = glueContext.write_dynamic_frame.from_options(
            frame=apply_mapping,
            connection_type="s3",
            connection_options={"path": s3path},
            format="parquet",
            transformation_ctx="s3sink")

# Read from Kinesis Data Stream
sourceData = glueContext.create_data_frame.from_catalog(
    database = GLUE_DATABASE, # "ventilatordb",
    table_name = GLUE_TABLE_NAME, # "ventilators_table",
    transformation_ctx = "datasource1",
    additional_options = {
        "startingPosition": STREAM_STARTING_POSITION,
        "inferSchema": "true"
    }
)

# sourceData1.printSchema()

glueContext.forEachBatch(frame=sourceData,
    batch_function=processBatch,
    options = {
        "windowSize": "100 seconds",
        "checkpointLocation": CHECKPOINT_LOCATION
    })

job.commit()
