
# Dynamic Partitioning in Kinesis Data Firehose: Creating partitioning keys with an AWS Lambda function

![firehose_dynamic_partition_with_lambda](./firehose_dynamic_partition_with_lambda.svg)

This is a kinesis data firehose dynamic partitioning project for Python development with CDK.

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

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all \
  --parameters FirehoseStreamName=<i>'your-delivery-stream-name'</i> \
  --parameters FirehosePrefix=<i>'your-s3-bucket-prefix-for-dynamic-partitioning'</i>
</pre>

### Creating partitioning keys with an AWS Lambda function

For example, let's define partitioning keys for it with an AWS Lambda function for the following sample data.

```
{
   "type": {
    "device": "mobile",
    "event": "view"
  },
  "customer_id": "123456789012",
  "event_timestamp": 1565382027, #epoch timestamp
  "region": "us-east-1"
}
```

You can transform, parse and return the data fields that you can then use for dynamic partitioning using the transform Lambda function.
For example, you are going to choose to partition your data based on `region`, `device`, and `event_timestamp`.
After selecting data parameters for your partitioning keys, you then extracts partioninig keys from the records with the AWS Lambda function in Python like this:

```python
# Get user payload
payload = base64.b64decode(firehose_record_input['data'])
json_value = json.loads(payload)

# Create output Firehose record and add modified payload and record ID to it.
event_timestamp = datetime.datetime.fromtimestamp(json_value['event_timestamp'])
partition_keys = {
  "region": json_value['region'],
  "device": json_value['type']['device'],
  "year": event_timestamp.strftime('%Y'),
  "month": event_timestamp.strftime('%m'),
  "day": event_timestamp.strftime('%d'),
  "hour": event_timestamp.strftime('%H')
}

# Create output Firehose record and add modified payload and record ID to it.
firehose_record_output = {
  'recordId': firehose_record_input['recordId'],
  'data': firehose_record_input['data'],
  'result': 'Ok',
  'metadata': { 'partitionKeys': partition_keys }
}

# Must set proper record ID
# Add the record to the list of output records.
firehose_records_output['records'].append(firehose_record_output)
```

Now you can create kinesis data firehose like this:

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all \
  --parameters FirehoseStreamName='PUT-S3-lambda' \
  --parameters FirehosePrefix='region=!{partitionKeyFromLambda:region}/device=!{partitionKeyFromLambda:device}/year=!{partitionKeyFromLambda:year}/month=!{partitionKeyFromLambda:month}/day=!{partitionKeyFromLambda:day}/hour=!{partitionKeyFromLambda:hour}/'
</pre>

List all CDK stacks with `cdk list` command before provisioning them.
<pre>
(.venv) $ cdk list
FirehoseDataProcLambdaStack
FirehoseToS3Stack
</pre>

Then, use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy -e FirehoseDataProcLambdaStack
(.venv) $ cdk deploy -e FirehoseToS3Stack \
  --parameters FirehoseStreamName=<i>'your-delivery-stream-name'</i> \
  --parameters FirehosePrefix=<i>'your-s3-bucket-prefix-for-dynamic-partitioning'</i>
</pre>

For example,
<pre>
(.venv) $ cdk deploy -e FirehoseDataProcLambdaStack
(.venv) $ cdk deploy -e FirehoseToS3Stack \
  --parameters FirehoseStreamName='PUT-S3-lambda' \
  --parameters FirehosePrefix='region=!{partitionKeyFromLambda:region}/device=!{partitionKeyFromLambda:device}/year=!{partitionKeyFromLambda:year}/month=!{partitionKeyFromLambda:month}/day=!{partitionKeyFromLambda:day}/hour=!{partitionKeyFromLambda:hour}/'
</pre>

After `cdk deploy` has been completed, you can check dynamic partitioning configuration of kinesis data firehose as running the following command:

<pre>
(.venv) $ aws firehose describe-delivery-stream \
  --delivery-stream-name <i>'your-delivery-stream-name'</i> \
  | jq '.DeliveryStreamDescription.Destinations[0].ExtendedS3DestinationDescription'
</pre>

For example,

<pre>
(.venv) $ aws firehose describe-delivery-stream \
  --delivery-stream-name PUT-S3-lambda \
  | jq '.DeliveryStreamDescription.Destinations[0].ExtendedS3DestinationDescription'

{
  "RoleARN": "arn:aws:iam::123456789012:role/service-role/KinesisFirehoseServiceRole-PUT-S3-lambda-us-east-1",
  "BucketARN": "arn:aws:s3:::firehose-to-s3-us-east-1-a4hzjvb",
  "Prefix": "region=!{partitionKeyFromLambda:region}/device=!{partitionKeyFromLambda:device}/year=!{partitionKeyFromLambda:year}/month=!{partitionKeyFromLambda:month}/day=!{partitionKeyFromLambda:day}/hour=!{partitionKeyFromLambda:hour}/",
  "ErrorOutputPrefix": "error/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/!{firehose:error-output-type}",
  "BufferingHints": {
    "SizeInMBs": 128,
    "IntervalInSeconds": 60
  },
  "CompressionFormat": "UNCOMPRESSED",
  "EncryptionConfiguration": {
    "NoEncryptionConfig": "NoEncryption"
  },
  "CloudWatchLoggingOptions": {
    "Enabled": true,
    "LogGroupName": "/aws/kinesisfirehose/PUT-S3-lambda",
    "LogStreamName": "DestinationDelivery"
  },
  "ProcessingConfiguration": {
    "Enabled": true,
    "Processors": [
      {
        "Type": "RecordDeAggregation",
        "Parameters": [
          {
            "ParameterName": "SubRecordType",
            "ParameterValue": "JSON"
          }
        ]
      },
      {
        "Type": "AppendDelimiterToRecord",
        "Parameters": []
      },
      {
        "Type": "Lambda",
        "Parameters": [
          {
            "ParameterName": "LambdaArn",
            "ParameterValue": "arn:aws:lambda:us-east-1:123456789012:function:MetadataExtractor:1"
          },
          {
            "ParameterName": "NumberOfRetries",
            "ParameterValue": "3"
          },
          {
            "ParameterName": "RoleArn",
            "ParameterValue": "arn:aws:iam::123456789012:role/service-role/KinesisFirehoseServiceRole-PUT-S3-lambda-us-east-1"
          },
          {
            "ParameterName": "BufferSizeInMBs",
            "ParameterValue": "3"
          },
          {
            "ParameterName": "BufferIntervalInSeconds",
            "ParameterValue": "300"
          }
        ]
      }
    ]
  },
  "S3BackupMode": "Disabled",
  "DataFormatConversionConfiguration": {
    "Enabled": false
  }
}
</pre>

### Verify

If you want to generate sample data and verify it is being processed and stored as follows: `Direct Put -> Kinesis Data Firehose -> S3`, <br/>
Run `gen_fake_firehose_data.py` script on the EC2 instance by entering the following command:

<pre>
(.venv) $ cd ..
(.venv) $ ls src/main/python/
gen_fake_firehose_data.py
(.venv) $ pip install boto3 Faker # pip install -r requirements.txt
(.venv) $ python src/main/python/gen_fake_firehose_data.py --stream-name <i>'your-delivery-stream-name'</i> --max-count -1
</pre>

If you would like to know more about the usage of this command, you can type

<pre>
(.venv) $ python src/main/python/gen_fake_firehose_data.py --help
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Clean Up

Delete the CloudFormation stack by running the below command.

```
(.venv) $ cdk destroy --force --all
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

## Learn more

 * [Dynamic Partitioning in Kinesis Data Firehose](https://docs.aws.amazon.com/firehose/latest/dev/dynamic-partitioning.html)
 * [Kinesis Data Firehose now supports dynamic partitioning to Amazon S3](https://aws.amazon.com/blogs/big-data/kinesis-data-firehose-now-supports-dynamic-partitioning-to-amazon-s3/)
 * [How to create a Lambda layer using a simulated Lambda environment with Docker](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-simulated-docker/)
 * [Kinesis Data Firehose Immersion Day](https://catalog.us-east-1.prod.workshops.aws/workshops/32e6bc9a-5c03-416d-be7c-4d29f40e55c4/en-US)
   * **Lab 3 - Customize partitioning of streaming data**

Enjoy!
