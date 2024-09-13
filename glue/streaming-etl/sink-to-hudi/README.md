
# AWS Glue Streaming ETL Job with Apace Hudi CDK Python project!

![glue-streaming-to-s3-with-hudi](./glue-streaming-data-to-hudi-table.svg)

This is an examplary AWS Glue Streaming ETL Job project for CDK development with Python.

This project is based on the AWS Big Data Blog titled ["Build a serverless pipeline to analyze streaming data using AWS Glue, Apache Hudi, and Amazon S3"](https://aws.amazon.com/ko/blogs/big-data/build-a-serverless-pipeline-to-analyze-streaming-data-using-aws-glue-apache-hudi-and-amazon-s3/) with [aws sample codes](https://github.com/aws-samples/aws-glue-streaming-etl-with-apache-hudi)

In this project, we create a streaming ETL job in AWS Glue to integrate Hudi with a streaming use case and create an in-place updatable data lake on Amazon S3.

After ingested to Amazon S3, you can query the data with [Amazon Athena](http://aws.amazon.com/athena).

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
(.venv) $ pip install -r requirements.txt
```

Before synthesizing the CloudFormation, **you first set up Apache Hudi connector for AWS Glue to use Apache Hudi with AWS Glue jobs.** (For more information, see [References](#references) (2))

Then you should set approperly the cdk context configuration file, `cdk.context.json`.

For example:
<pre>
{
  "kinesis_stream_name": "hudi-demo-stream",
  "glue_assets_s3_bucket_name": "aws-glue-assets-123456789012-us-east-1",
  "glue_job_script_file_name": "glue_hudi_streaming_from_kds_to_s3.py",
  "glue_job_name": "hudi-streaming-from-kds-to-s3",
  "glue_job_input_arguments": {
    "--spark_checkpoint_s3_path": "s3://hudi-demo-bucket-atq4q5u/spark_checkpoints/",
    "--s3_path_hudi": "s3://hudi-demo-bucket-atq4q5u/hudi_stuff/hudi_demo_table_cow/",
    "--database_name": "hudi_demo_db",
    "--hudi_table_name": "hudi_demo_table_cow",
    "--kinesis_table_name": "hudi_demo_kinesis_stream_table",
    "--starting_position_of_kinesis_iterator": "LATEST",
    "--window_size": "10 seconds"
  },
  "glue_connections_name": "hudi-connection"
}
</pre>

:warning: **You should create a S3 bucket for a glue job script and upload the glue job script file into the s3 bucket.**
At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Run Test

1. Set up **Apache Hudi connector for AWS Glue** to use Apache Hudi with AWS Glue jobs.
2. Create a Kinesis data stream
   <pre>
   (.venv) $ cdk deploy KinesisStreamAsGlueStreamingJobDataSource
   </pre>
3. Define a schema for the streaming data
   <pre>
   (.venv) $ cdk deploy GlueSchemaOnKinesisStream
   </pre>

   Running `cdk deploy GlueSchemaOnKinesisStream` command is like that we create a schema manually using the AWS Glue Data Catalog as the following steps:

   (1) On the AWS Glue console, choose **Data Catalog**.<br/>
   (2) Choose **Databases**, and click **Add database**.<br/>
   (3) Create a database with the name `hudi_demo_db`.<br/>
   (4) On the **Data Catalog** menu, Choose **Tables**, and click **Add Table**.<br/>
   (5) For the table name, enter `hudi_demo_kinesis_stream_table`.<br/>
   (6) Select `hudi_demo_db` as a database.<br/>
   (7) Choose **Kinesis** as the type of source.<br/>
   (8) Enter the name of the stream.<br/>
   (9) For the classification, choose **JSON**.<br/>
   (10) Choose **Finish**

4. Create Glue Streaming Job
   <pre>
   (.venv) $ ls src/main/python/
    glue_hudi_streaming_from_kds_to_s3.py
   (.venv) $ aws s3 mb <i>s3://aws-glue-assets-123456789012-us-east-1</i> --region <i>us-east-1</i>
   (.venv) $ aws s3 cp src/main/python/glue_hudi_streaming_from_kds_to_s3.py <i>s3://aws-glue-assets-123456789012-us-east-1/scripts/</i>
   (.venv) $ cdk deploy GlueStreamingSinkToHudiJobRole GrantLFPermissionsOnGlueJobRole GlueStreamingSinkToHudi
   </pre>
5. Make sure the glue job to access the Kinesis Data Streams table in the Glue Catalog database, otherwise grant the glue job to permissions

   We can get permissions by running the following command:
   <pre>
   (.venv) $ aws lakeformation list-permissions | jq -r '.PrincipalResourcePermissions[] | select(.Principal.DataLakePrincipalIdentifier | endswith(":role/GlueStreamingJobRole"))'
   </pre>
   If not found, we need manually to grant the glue job to required permissions by running the following command:
   <pre>
   (.venv) $ aws lakeformation grant-permissions \
               --principal DataLakePrincipalIdentifier=arn:aws:iam::<i>{account-id}</i>:role/<i>GlueStreamingJobRole</i> \
               --permissions SELECT DESCRIBE ALTER INSERT DELETE \
               --resource '{ "Table": {"DatabaseName": "<i>hudi_demo_db</i>", "TableWildcard": {}} }'
   </pre>
6. Create a table with partitioned data in Amazon Athena

   Go to [Athena](https://console.aws.amazon.com/athena/home) on the AWS Management console.<br/>
   * (step 1) Create a database

     In order to create a new database called `hudi_demo_db`, enter the following statement in the Athena query editor
     and click the **Run** button to execute the query.

     <pre>
     CREATE DATABASE IF NOT EXISTS hudi_demo_db
     </pre>

    * (step 2) Create a table

      Copy the following query into the Athena query editor, replace the `xxxxxxx` in the last line under `LOCATION` with the string of your S3 bucket, and execute the query to create a new table.
      <pre>
      CREATE EXTERNAL TABLE hudi_demo_db.hudi_demo_table_cow (
        `_hoodie_commit_time` string,
        `_hoodie_commit_seqno` string,
        `_hoodie_record_key` string,
        `_hoodie_partition_path` string,
        `_hoodie_file_name` string,
        `date` string,
        `column_to_update_integer` int,
        `column_to_update_string` string)
      PARTITIONED BY (
        `name` string,
        `year` string,
        `month` string,
        `day` string)
      ROW FORMAT SERDE
        'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
      STORED AS INPUTFORMAT
        'org.apache.hudi.hadoop.HoodieParquetInputFormat'
      OUTPUTFORMAT
        'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
      LOCATION
        's3://hudi-demo-bucket-<i>xxxxx</i>/hudi_stuff/hudi_demo_table_cow';
      </pre>
      If the query is successful, a table named `hudi_demo_table_cow` is created and displayed on the left panel under the **Tables** section.

      If you get an error, check if (a) you have updated the `LOCATION` to the correct S3 bucket name, (b) you have mydatabase selected under the Database dropdown, and (c) you have `AwsDataCatalog` selected as the **Data source**.

      :information_source: If you fail to create the table, give Athena users access permissions on `hudi_demo_db` through [AWS Lake Formation](https://console.aws.amazon.com/lakeformation/home), or you can grant anyone using Athena to access `hudi_demo_db` by running the following command:
      <pre>
      (.venv) $ aws lakeformation grant-permissions \
              --principal DataLakePrincipalIdentifier=arn:aws:iam::<i>{account-id}</i>:user/<i>example-user-id</i> \
              --permissions CREATE_TABLE DESCRIBE ALTER DROP \
              --resource '{ "Database": { "Name": "<i>hudi_demo_db</i>" } }'
      (.venv) $ aws lakeformation grant-permissions \
              --principal DataLakePrincipalIdentifier=arn:aws:iam::<i>{account-id}</i>:user/<i>example-user-id</i> \
              --permissions SELECT DESCRIBE ALTER INSERT DELETE DROP \
              --resource '{ "Table": {"DatabaseName": "<i>hudi_demo_db</i>", "TableWildcard": {}} }'
      </pre>

7. Run glue job to load data from Kinesis Data Streams into S3
   <pre>
   (.venv) $ aws glue start-job-run --job-name <i>hudi-streaming-from-kds-to-s3</i>
   </pre>
8. Generate streaming data

   We can synthetically generate ventilator data in JSON format using a simple Python application.
   <pre>
   (.venv) $ python src/utils/gen_fake_kinesis_stream_data.py \
               --region-name <i>us-east-1</i> \
               --stream-name <i>your-stream-name</i> \
               --max-count 1000
   </pre>
9. Check streaming data in S3

   After `5~10` minutes, you can see that the streaming data have been delivered from **Kinesis Data Streams** to **S3**.

   ![glue-streaming-data-in-s3-with-hudi](./assets/glue-streaming-data-in-s3-with-hudi.png)

10. Load partitioned data into Amazon Athena table

    Go to [Athena](https://console.aws.amazon.com/athena/home) on the AWS Management console.

    * (step 1) Check partitions

      Run the following query to list all the partitions in an Athena table in unsorted order.
      <pre>
      SHOW PARTITIONS hudi_demo_db.hudi_demo_table_cow;
      </pre>

    * (step 2) Load the partition data

      If no partitions are found, we can use the `ALTER TABLE ADD PARTITION` command to add each partition manually.
      For example, to load the data in `s3://hudi-demo-bucket-xxxxxx/hudi_stuff/hudi_demo_table_cow/name=Person1/year=2023/month=01/day=10`, you can run the following query.
      <pre>
      ALTER TABLE hudi_demo_db.hudi_demo_table_cow ADD IF NOT EXISTS
      PARTITION (name='Person1', year='2023', month='01', day='10')
      LOCATION 's3://hudi-demo-bucket-<i>xxxxxx</i>/hudi_stuff/hudi_demo_table_cow/name=Person1/year=2023/month=01/day=10'
      PARTITION (name='Person2', year='2023', month='01', day='10')
      LOCATION 's3://hudi-demo-bucket-<i>xxxxxx</i>/hudi_stuff/hudi_demo_table_cow/name=Person1/year=2023/month=01/day=10'
      PARTITION (name='Person3', year='2023', month='01', day='10')
      LOCATION 's3://hudi-demo-bucket-<i>xxxxxx</i>/hudi_stuff/hudi_demo_table_cow/name=Person1/year=2023/month=01/day=10';
      </pre>
      After you run this command, the data is ready for querying.

11. Run test query

    Enter the following SQL statement and execute the query.
    <pre>
    SELECT COUNT(*)
    FROM hudi_demo_db.hudi_demo_table_cow;
    </pre>

## Clean Up

1. Stop the glue job by replacing the job name in below command.

   <pre>
   (.venv) $ JOB_RUN_IDS=$(aws glue get-job-runs \
              --job-name hudi-streaming-from-kds-to-s3 | jq -r '.JobRuns[] | select(.JobRunState=="RUNNING") | .Id' \
              | xargs)
   (.venv) $ aws glue batch-stop-job-run \
              --job-name hudi-streaming-from-kds-to-s3 \
              --job-run-ids $JOB_RUN_IDS
   </pre>

2. Delete the CloudFormation stack by running the below command.

   <pre>
   (.venv) $ cdk destroy --all
   </pre>

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

## References

 * (1) [AWS Glue versions](https://docs.aws.amazon.com/glue/latest/dg/release-notes.html): The AWS Glue version determines the versions of Apache Spark and Python that AWS Glue supports.
   | AWS Glue version	| Hudi | Delta Lake	| Iceberg |
   |------------------|------|------------|---------|
   | AWS Glue 3.0	| 0.10.1 | 1.0.0 | 0.13.1 |
   | AWS Glue 4.0	| 0.12.1 | 2.1.0 | 1.0.0  |
 * (2) [Build a serverless pipeline to analyze streaming data using AWS Glue, Apache Hudi, and Amazon S3 (2022-03-09)](https://aws.amazon.com/ko/blogs/big-data/build-a-serverless-pipeline-to-analyze-streaming-data-using-aws-glue-apache-hudi-and-amazon-s3/)
 * (3) [aws-samples/aws-glue-streaming-etl-with-apache-hudi](https://github.com/aws-samples/aws-glue-streaming-etl-with-apache-hudi)
 * (4) [Using Amazon Athena to query Apache Hudi datasets](https://docs.aws.amazon.com/athena/latest/ug/querying-hudi.html)
 * (5) [Streaming ETL jobs in AWS Glue](https://docs.aws.amazon.com/glue/latest/dg/add-job-streaming.html)
 * (6) [Crafting serverless streaming ETL jobs with AWS Glue (2020-10-14)](https://aws.amazon.com/ko/blogs/big-data/crafting-serverless-streaming-etl-jobs-with-aws-glue/)
 * (7) [Apache Hudi Quick start - Spark Guide](https://hudi.apache.org/docs/quick-start-guide/)

## Troubleshooting

 * Granting database or table permissions error using AWS CDK
   * Error message:
     <pre>
     AWS::LakeFormation::PrincipalPermissions | CfnPrincipalPermissions Resource handler returned message: "Resource does not exist or requester is not authorized to access requested permissions. (Service: LakeFormation, Status Code: 400, Request ID: f4d5e58b-29b6-4889-9666-7e38420c9035)" (RequestToken: 4a4bb1d6-b051-032f-dd12-5951d7b4d2a9, HandlerErrorCode: AccessDenied)
     </pre>
   * Solution:

     The role assumed by cdk is not a data lake administrator. (e.g., `cdk-hnb659fds-deploy-role-123456789012-us-east-1`) <br/>
     So, deploying PrincipalPermissions meets the error such as:

     `Resource does not exist or requester is not authorized to access requested permissions.`

     In order to solve the error, it is necessary to promote the cdk execution role to the data lake administrator.<br/>
     For example, https://github.com/aws-samples/data-lake-as-code/blob/mainline/lib/stacks/datalake-stack.ts#L68

   * Reference:

     [https://github.com/aws-samples/data-lake-as-code](https://github.com/aws-samples/data-lake-as-code) - Data Lake as Code
 * Amazon Athena experienced a permission error in Amazon Athena
   * Error message:
     <pre>
     [ErrorCategory:USER_ERROR, ErrorCode:PERMISSION_ERROR], Detail:Amazon Athena experienced a permission error.
     Please provide proper permission and submitting the query again. If the issue reoccurs, contact AWS support for further assistance.
     You will not be charged for this query. We apologize for the inconvenience., Message:Amazon Athena experienced a permission error.
     Please provide proper permission and submitting the query again. If the issue reoccurs, contact AWS support for further assistance.
     You will not be charged for this query. We apologize for the inconvenience.
     This query ran against the "hudi_demo_db" database, unless qualified by the query.
     Please post the error message on our forum  or contact customer support  with Query Id: 8a61dc7c-02f0-4552-8a5c-940080d78ac7
     </pre>
   * Solution:

     If you fail to create the table, give Athena users access permissions on `hudi_demo_db` through [AWS Lake Formation](https://console.aws.amazon.com/lakeformation/home), or you can grant anyone using Athena to access `hudi_demo_db` by running the following command:
      <pre>
      (.venv) $ aws lakeformation grant-permissions \
              --principal DataLakePrincipalIdentifier=arn:aws:iam::<i>{account-id}</i>:user/<i>example-user-id</i> \
              --permissions CREATE_TABLE DESCRIBE ALTER DROP \
              --resource '{ "Database": { "Name": "<i>hudi_demo_db</i>" } }'
      (.venv) $ aws lakeformation grant-permissions \
              --principal DataLakePrincipalIdentifier=arn:aws:iam::<i>{account-id}</i>:user/<i>example-user-id</i> \
              --permissions SELECT DESCRIBE ALTER INSERT DELETE DROP \
              --resource '{ "Table": {"DatabaseName": "<i>hudi_demo_db</i>", "TableWildcard": {}} }'
      </pre>
