import sys
import datetime
import boto3
import base64

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

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'aws_region', 'output_path'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# S3 sink locations
aws_region = args['aws_region']
output_path = args['output_path']

s3_target = output_path + "ventilator_metrics"
checkpoint_location = output_path + "cp/"
temp_path = output_path + "temp/"

def processBatch(data_frame, batchId):
    now = datetime.datetime.now()

    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    minute = now.minute

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

        dynamic_frame.printSchema()

        # Write to S3 Sink
        s3path = s3_target + "/ingest_year={year:0>4}/ingest_month={month:0>2}/ingest_day={day:0>2}/ingest_hour={hour:0>2}/".format(year=year, month=month, day=day, hour=hour)
        s3sink = glueContext.write_dynamic_frame.from_options(frame=apply_mapping, connection_type="s3",
            connection_options={"path": s3path}, format="parquet", transformation_ctx="s3sink")

# Read from Kinesis Data Stream
sourceData1 = glueContext.create_data_frame.from_catalog(
    database = "ventilatordb",
    table_name = "ventilators_table",
    transformation_ctx = "datasource1",
    additional_options = {"startingPosition": "TRIM_HORIZON", "inferSchema": "true"})

sourceData1.printSchema()

# sourceData2 = glueContext.create_data_frame.from_catalog(
#     database = "ventilatordb",
#     table_name = "ventilators_table2",
#     transformation_ctx = "datasource2",
#     additional_options = {"startingPosition": "TRIM_HORIZON", "inferSchema": "true"})

# sourceData2.printSchema()

glueContext.forEachBatch(frame=sourceData1,
    batch_function=processBatch,
    options = {
        "windowSize": "100 seconds",
        "checkpointLocation": checkpoint_location
    })

job.commit()