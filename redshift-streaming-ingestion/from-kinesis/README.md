
# Amazon Redshift Streaming Ingestion from Kinesis Data Streams CDK Python project!

![redshift_streaming_ingestion_from_kinesis_data_streams](./redshift_streaming_from_kds.svg)

This is an Amazon Redshift Streaming Ingestion from Kinesis Data Streams project for CDK development with Python.

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
$ pip install -r requirements.txt
```

:information_source: Before you deploy this project, you should create an AWS Secret for your Redshift Serverless Admin user. You can create an AWS Secret like this:

<pre>
$ aws secretsmanager create-secret \
    --name "<i>your_redshift_secret_name</i>" \
    --description "<i>(Optional) description of the secret</i>" \
    --secret-string '{"admin_username": "admin", "admin_user_password": "<i>password_of_at_last_8_characters</i>"}'
</pre>

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all \
              -c vpc_name='<i>your-existing-vpc-name</i>' \
              -c aws_secret_name='<i>your_redshift_secret_name</i>'
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy --all \
              -c vpc_name='<i>your-existing-vpc-name</i>' \
              -c aws_secret_name='<i>your_redshift_secret_name</i>'
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Clean Up

Delete the CloudFormation stack by running the below command.

<pre>
(.venv) $ cdk destroy --force --all \
              -c vpc_name='<i>your-existing-vpc-name</i>' \
              -c aws_secret_name='<i>your_redshift_secret_name</i>'
</pre>

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## Run Test

#### Amazon Redshift setup

These steps show you how to configure the materialized view to ingest data.

1. Connect to the Redshift query editor v2

   ![redshift-query-editor-v2-connection](./redshift-query-editor-v2-connection.png)

2. Create an external schema to map the data from Kinesis to a Redshift object.
   <pre>
   CREATE EXTERNAL SCHEMA evdata FROM KINESIS
   IAM_ROLE 'arn:aws:iam::<i>{AWS-ACCOUNT-ID}</i>:role/RedshiftStreamingRole';
   </pre>
   For information about how to configure the IAM role, see [Getting started with streaming ingestion from Amazon Kinesis Data Streams](https://docs.aws.amazon.com/redshift/latest/dg/materialized-view-streaming-ingestion-getting-started.html).

3. Create a materialized view to consume the stream data.

   Note that Kinesis stream names are case-sensitive and can contain both uppercase and lowercase letters. To use case-sensitive identifiers, you can set the configuration setting `enable_case_sensitive_identifier` to true at either the session or cluster level.
   <pre>
   -- To create and use case sensitive identifiers
   SET enable_case_sensitive_identifier TO true;

   -- To check if enable_case_sensitive_identifier is turned on
   SHOW enable_case_sensitive_identifier;
   </pre>

   The following example defines a materialized view with JSON source data.<br/>
   Create the materialized view so it’s distributed on the UUID value from the stream and is sorted by the `refresh_time` value. The `refresh_time` is the start time of the materialized view refresh that loaded the record. The materialized view is set to auto refresh and will be refreshed as data keeps arriving in the stream.
   <pre>
   CREATE MATERIALIZED VIEW ev_station_data_extract DISTKEY(6) sortkey(1) AUTO REFRESH YES AS
    SELECT refresh_time,
       approximate_arrival_timestamp,
       partition_key,
       shard_id,
       sequence_number,
       json_extract_path_text(from_varbyte(kinesis_data,'utf-8'),'_id',true)::character(36) as ID,
       json_extract_path_text(from_varbyte(kinesis_data,'utf-8'),'clusterID',true)::varchar(30) as clusterID,
       json_extract_path_text(from_varbyte(kinesis_data,'utf-8'),'connectionTime',true)::varchar(20) as connectionTime,
       json_extract_path_text(from_varbyte(kinesis_data,'utf-8'),'kWhDelivered',true)::DECIMAL(10,2) as kWhDelivered,
       json_extract_path_text(from_varbyte(kinesis_data,'utf-8'),'stationID',true)::INTEGER as stationID,
       json_extract_path_text(from_varbyte(kinesis_data,'utf-8'),'spaceID',true)::varchar(100) as spaceID,
       json_extract_path_text(from_varbyte(kinesis_data, 'utf-8'),'timezone',true)::varchar(30)as timezone,
       json_extract_path_text(from_varbyte(kinesis_data,'utf-8'),'userID',true)::varchar(30) as userID
    FROM evdata."ev_stream_data"
    WHERE LENGTH(kinesis_data) < 65355;
   </pre>
   The code above filters records larger than **65355** bytes. This is because `json_extract_path_text` is limited to varchar data type. The Materialized view should be defined so that there aren’t any type conversion errors.

4. Refreshing materialized views for streaming ingestion

   The materialized view is auto-refreshed as long as there is new data on the KDS stream. You can also disable auto-refresh and run a manual refresh or schedule a manual refresh using the Redshift Console UI.<br/>
   To update the data in a materialized view, you can use the `REFRESH MATERIALIZED VIEW` statement at any time.
   <pre>
   REFRESH MATERIALIZED VIEW ev_station_data_extract;
   </pre>

#### Query the stream

1. Query data in the materialized view.
   <pre>
   SELECT *
   FROM ev_station_data_extract;
   </pre>
2. Query the refreshed materialized view to get usage statistics.
   <pre>
   SELECT to_timestamp(connectionTime, 'YYYY-MM-DD HH24:MI:SS') as connectiontime
      ,SUM(kWhDelivered) AS Energy_Consumed
      ,count(distinct userID) AS #Users
   FROM ev_station_data_extract
   GROUP BY to_timestamp(connectionTime, 'YYYY-MM-DD HH24:MI:SS')
   ORDER BY 1 DESC;
   </pre>


## References

 * [Amazon Redshift - Getting started with streaming ingestion from Amazon Kinesis Data Streams](https://docs.aws.amazon.com/redshift/latest/dg/materialized-view-streaming-ingestion-getting-started.html)
 * [Amazon Redshift - Electric vehicle station-data streaming ingestion tutorial, using Kinesis](https://docs.aws.amazon.com/redshift/latest/dg/materialized-view-streaming-ingestion-example-station-data.html)
 * [Amazon Redshift Configuration Reference - enable_case_sensitive_identifier](https://docs.aws.amazon.com/redshift/latest/dg/r_enable_case_sensitive_identifier.html)
 * [Real-time analytics with Amazon Redshift streaming ingestion (2022-04-27)](https://aws.amazon.com/ko/blogs/big-data/real-time-analytics-with-amazon-redshift-streaming-ingestion/)
  ![](https://d2908q01vomqb2.cloudfront.net/b6692ea5df920cad691c20319a6fffd7a4a766b8/2022/04/14/BDB-2193-image001.png)
 * [Mimesis: Fake Data Generator](https://mimesis.name/en/latest/index.html) - Mimesis is a high-performance fake data generator for Python, which provides data for a variety of purposes in a variety of languages

