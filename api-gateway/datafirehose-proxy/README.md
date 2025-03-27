
# Create a REST API as an Amazon Data Firehose proxy in API Gateway

This repository shows you how to integrate Amazon API Gateway with Amazon Data Firehose by implementing a simple [web analytics](https://en.wikipedia.org/wiki/Web_analytics) system using CDK scripts and sample code.

Below diagram shows what we are implementing.

![web-analytics-arch](web-analytics-datafirehose-iceberg-arch.svg)

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

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

### Upload Lambda Layer code

Before deployment, you should uplad zipped code files to s3 like this:
<pre>
(.venv) $ aws s3api create-bucket --bucket <i>your-s3-bucket-name-for-lambda-layer-code</i> --region <i>region-name</i>
(.venv) $ ./build-aws-lambda-layer-package.sh <i>your-s3-bucket-name-for-lambda-layer-code</i>
</pre>

> :warning: To create a bucket outside of the `us-east-1` region, `aws s3api create-bucket` command requires the appropriate **LocationConstraint** to be specified in order to create the bucket in the desired region. For more information, see these [examples](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/s3api/create-bucket.html#examples).

> :warning: Make sure you have **Docker** installed.

For example,
<pre>
(.venv) $ aws s3api create-bucket --bucket lambda-layer-resources --region <i>us-east-1</i>
(.venv) $ ./build-aws-lambda-layer-package.sh lambda-layer-resources
</pre>

For more information about how to create a package for Amazon Lambda Layer, see [here](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-simulated-docker/).

### Deploy

Before to synthesize the CloudFormation template for this code, you should update `cdk.context.json` file.<br/>
In particular, you need to fill the s3 location of the previously created lambda lay codes.

For example,
<pre>
{
  "firehose_data_tranform_lambda": {
    "s3_bucket_name": "<i>lambda-layer-resources</i>",
    "s3_object_key": "<i>var/fastavro-lib-1.10.0-py-3.11.zip</i>"
  },
  "data_firehose_configuration": {
    "stream_name": "Firehose-To-Iceberg-Demo",
    "buffering_hints": {
      "interval_in_seconds": 60,
      "size_in_mbs": 128
    },
    "transform_records_with_aws_lambda": {
      "buffer_size": 3,
      "buffer_interval": 300,
      "number_of_retries": 3
    },
    "destination_iceberg_table_configuration": {
      "database_name": "demo_iceberg_db",
      "table_name": "demo_iceberg"
    },
    "output_prefix": "demo_iceberg_db/demo_iceberg",
    "error_output_prefix": "error/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/!{firehose:error-output-type}"
  }
}
</pre>
:information_source: `database_name`, and `table_name` of `data_firehose_configuration.destination_iceberg_table_configuration` is used in [**Set up Delivery Stream**](#set-up-delivery-stream) step.

:information_source: When updating or deleting records in an Iceberg table, specify the table's primary key column name as `unique_keys` in the `data_firehose_configuration.destination_iceberg_table_configuration` settings.
For example,
<pre>
"destination_iceberg_table_configuration": {
  "database_name": "demo_iceberg_db",
  "table_name": "demo_iceberg",
  "unique_keys": [
    "user_id", "timestamp"
  ]
}
</pre>


Now you are ready to synthesize the CloudFormation template for this code.<br/>

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all
</pre>

Now let's try to deploy.

## List all CDK Stacks

```
(.venv) $ cdk list
DataFirehoseProxyApiGw
DataFirehoseToIcebergS3Path
DataFirehoseTransformLambdaStack
DataFirehoseToIcebergRoleStack
GrantLFPermissionsOnFirehoseRole
DataFirehoseToIcebergStack
```

Use `cdk deploy` command to create the stack shown above.

## Create API endpoint for web data collection

<pre>
(.venv) $ cdk deploy --require-approval never DataFirehoseProxyApiGw
</pre>

## Set up Delivery Stream

1. Create a S3 bucket for Apache Iceberg table
   <pre>
   (.venv) $ cdk deploy --require-approval never DataFirehoseToIcebergS3Path
   </pre>
2. Create a table with partitioned data in Amazon Athena

   Go to [Athena](https://console.aws.amazon.com/athena/home) on the AWS Management console.<br/>
   * (step 1) Create a database

      In order to create a new database called `demo_iceberg_db`, enter the following statement in the Athena query editor and click the **Run** button to execute the query.

      <pre>
      CREATE DATABASE IF NOT EXISTS demo_iceberg_db;
      </pre>

   * (step 2) Create a table

      Copy the following query into the Athena query editor.

      Update `LOCATION` to your S3 bucket name and execute the query to create a new table.
      <pre>
      CREATE TABLE demo_iceberg_db.demo_iceberg (
        `user_id` string,
        `session_id` string,
        `event` string,
        `referrer` string,
        `user_agent` string,
        `ip` string,
        `hostname` string,
        `os` string,
        `timestamp` timestamp,
        `uri` string
      )
      PARTITIONED BY (event)
      LOCATION 's3://datafirehose-proxy-<i>{region}</i>-</i>{account_id}</i>/demo_iceberg_db/demo_iceberg'
      TBLPROPERTIES (
        'table_type'='iceberg',
        'format'='parquet',
        'write_compression'='snappy',
        'optimize_rewrite_delete_file_threshold'='10'
      );
      </pre>
      If the query is successful, a table named `demo_iceberg` is created and displayed on the left panel under the **Tables** section.

      If you get an error, check if (a) you have updated the `LOCATION` to the correct S3 bucket name, (b) you have `demo_iceberg_db` selected under the Database dropdown, and (c) you have `AwsDataCatalog` selected as the **Data source**.
3. Create a lambda function to process the streaming data.
   <pre>
   (.venv) $ cdk deploy --require-approval never DataFirehoseTransformLambdaStack
   </pre>
4. To allow Data Firehose to ingest data into the Apache Iceberg table, create an IAM role and grant permissions to the role.
   <pre>
   (.venv) $ cdk deploy --require-approval never \
                 DataFirehoseToIcebergRoleStack \
                 GrantLFPermissionsOnFirehoseRole
   </pre>

   :information_source: If you fail to create the table, give Athena users access permissions on `demo_iceberg_db` through [AWS Lake Formation](https://console.aws.amazon.com/lakeformation/home), or you can grant Amazon Data Firehose to access `demo_iceberg_db` by running the following command:
   <pre>
   (.venv) $ aws lakeformation grant-permissions \
                 --principal DataLakePrincipalIdentifier=arn:aws:iam::<i>{account-id}</i>:role/<i>role-id</i> \
                 --permissions CREATE_TABLE DESCRIBE ALTER DROP \
                 --resource '{ "Database": { "Name": "<i>demo_iceberg_db</i>" } }'
   (.venv) $ aws lakeformation grant-permissions \
                 --principal DataLakePrincipalIdentifier=arn:aws:iam::<i>{account-id}</i>:role/<i>role-id</i> \
                 --permissions SELECT DESCRIBE ALTER INSERT DELETE DROP \
                 --resource '{ "Table": {"DatabaseName": "<i>demo_iceberg_db</i>", "TableWildcard": {}} }'
   </pre>
5. Deploy Amazon Data Firehose.
   <pre>
   (.venv) $ cdk deploy --require-approval never DataFirehoseToIcebergStack
   </pre>

## Run Test

1. Run `GET /streams` method to invoke `ListDeliveryStreams` in Amazon Data Firehose
   <pre>
   $ curl -X GET https://<i>your-api-gateway-id</i>.execute-api.us-east-1.amazonaws.com/v1/streams
   </pre>

   The response is:
   <pre>
   {
     "DeliveryStreamNames": [
       "Firehose-To-Iceberg-Demo"
     ],
     "HasMoreDeliveryStreams": false
   }
   </pre>

2. Generate test data.
   <pre>
   (.venv) $ pip install -r requirements-dev.txt
   (.venv) $ python src/utils/gen_fake_data.py \
                 --stream-name <i>Firehose-To-Iceberg-Demo</i> \
                 --api-url 'https://<i>your-api-gateway-id</i>.execute-api.us-east-1.amazonaws.com/v1' \
                 --api-method records \
                 --max-count 5

   [200 OK] {"Encrypted":false,"FailedPutCount":0,"RequestResponses":[{"RecordId":"NxB5xOO4Y30ppGBZFfpDoREir/dcWwsF1j4NAie9K1N5pqpjZCSkJPM+7I+Wx7gB/H6hS1BUFGLVIQlR/xEsi7WzT6uA/JX4nXndcF7gxhn3UFGEyyFcgDXyjot5lCFJ5UNnhJk8gAeYT0Ghxj3BNTI22hgrfqdDnjo5MoAg8/0us408pDL37EF4DpIkFMAXWdZdwLRcS6cDt0o0XADBV17XwJnilrSv"}]}
   [200 OK] {"Encrypted":false,"FailedPutCount":0,"RequestResponses":[{"RecordId":"slrDNLj+LPl1BAi6LzUVvUrhICOdnBY48gIG09zDGb/8fJElu3pYyTdfdNk9V+06rHz/ZY9RoV/0+UapEHaDDVqSjeDQZyZx0HeB2UDVP167Iv1DMgDvDIAiVlwcAyEsfUloqtRekM/B4NHEteJvCrPpqeQV8kYqk6EE1yJvJiLhBnyTVEuoVWbW4qiD+djsgijfL4EufK4ahdQN+CYs70HdUTEdQiV0"}]}
   [200 OK] {"Encrypted":false,"FailedPutCount":0,"RequestResponses":[{"RecordId":"WGUixKjKAE3aXVe3FbhoRGVh1WomWht8/S1lqhUa6IhxN+tskX5xxO3PjsukPSDDMd9J5LwfzwSh7tt9PQMaqh2r6JDTvP3X3wFItGGrhqY6UD52zs/Z9WINpa1HWcl677xk/qec61gvD5QOpTXWmfG2Q/uWwuboIHoKIqigxeqMpsRpPH40TA6m0HF9AJVrZ5a2VI+OhEK9V/5VkaTI5aQ+Gltl/TSj"}]}
   [200 OK] {"Encrypted":false,"FailedPutCount":0,"RequestResponses":[{"RecordId":"sOiJXXhDffAuoLaOm7E3y/8GIb9bwVbqrUcfotKT4H2iVQs3sPO1BxVwuaCMpfL8sQwpL4TSg5Y3EfLOzjrGlEOa4D14a3GAuffMQSEBVlwuJDED4JcFHJ/ltekVK/pMyejbBjyVk4e+S1oFK1LaXiGrcrVJ6XzJBk/NDnRLxGLYy+takFZMfyaStcZxXonnmdqw8YwWGgGnsbwj2nGVkR9PBWdyh41l"}]}
   </pre>

3. Check streaming data in S3

   After `5~10` minutes, you can see that the streaming data have been delivered from **Data Firehose** to **S3**.

   ![iceberg-table](./assets/demo-iceberg-table.png)
   ![iceberg-table-data-level-01](./assets/demo-iceberg-data-level-01.png)
   ![iceberg-table-data-level-02](./assets/demo-iceberg-data-level-02.png)
   ![iceberg-table-data-level-03](./assets/demo-iceberg-data-level-03.png)

4. Run test query using Amazon Athena

   Go to [Athena](https://console.aws.amazon.com/athena/home) on the AWS Management console.

   * (Step 1) Specify the workgroup to use

     To run queries, switch to the appropriate workgroup like this:
      ![amazon-athena-switching-to-workgroup](./assets/amazon-athena-switching-to-workgroup.png)

   * (Step 2) Run test query

     Enter the following SQL statement and execute the query.
     <pre>
     SELECT COUNT(*)
     FROM demo_iceberg_db.demo_iceberg;
     </pre>

## Clean Up

Delete the CloudFormation stack by running the below command.
<pre>
(.venv) $ cdk destroy --force --all
</pre>


## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

 * [Web Analytics](https://en.wikipedia.org/wiki/Web_analytics)
 * [Tutorial: Create a REST API as an Amazon Kinesis proxy in API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/integrating-api-with-aws-services-kinesis.html)
 * [Streaming Data Solution for Amazon Kinesis](https://aws.amazon.com/ko/solutions/implementations/aws-streaming-data-solution-for-amazon-kinesis/)
   <div>
     <img src="https://d1.awsstatic.com/Solutions/Solutions%20Category%20Template%20Draft/Solution%20Architecture%20Diagrams/aws-streaming-data-using-api-gateway-architecture.1b9d28f061fe84385cb871ec58ccad18c7265d22.png", alt with="385" height="204">
   </div>
 * [(AWS Developer Guide) Deliver data to Apache Iceberg Tables with Amazon Data Firehose](https://docs.aws.amazon.com/firehose/latest/dev/apache-iceberg-destination.html)
 * [Building fine-grained authorization using Amazon Cognito, API Gateway, and IAM](https://aws.amazon.com/ko/blogs/security/building-fine-grained-authorization-using-amazon-cognito-api-gateway-and-iam/)
 * [AWS Lake Formation - Create a data lake administrator](https://docs.aws.amazon.com/lake-formation/latest/dg/getting-started-setup.html#create-data-lake-admin)
 * [AWS Lake Formation Permissions Reference](https://docs.aws.amazon.com/lake-formation/latest/dg/lf-permissions-reference.html)
 * [Amazon Athena Using Iceberg tables](https://docs.aws.amazon.com/athena/latest/ug/querying-iceberg.html)
 * [Amazon Athena Workshop](https://athena-in-action.workshop.aws/)
 * [Curl Cookbook](https://catonmat.net/cookbooks/curl)
 * [fastavro](https://fastavro.readthedocs.io/) - Fast read/write of `AVRO` files
 * [Apache Avro Specification](https://avro.apache.org/docs/current/spec.html)
 * [How to create a Lambda layer using a simulated Lambda environment with Docker](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-simulated-docker/)
   ```
   $ cat <<EOF > requirements-Lambda-Layer.txt
   > fastavro==1.6.1
   > EOF
   $ docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.11" /bin/sh -c "pip install -r requirements-Lambda-Layer.txt -t python/lib/python3.11/site-packages/; exit"
   $ zip -r fastavro-lib.zip python > /dev/null
   $ aws s3 mb s3://my-bucket-for-lambda-layer-packages
   $ aws s3 cp fastavro-lib.zip s3://my-bucket-for-lambda-layer-packages/
   ```
