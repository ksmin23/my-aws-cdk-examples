# Amazon Kinesis Data Firehose with Data Transformation

![firehose_data_transform](./firehose_data_transform.svg)

This is a data transform in kinesis data firehose for Python development with CDK.

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
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
(.venv) $ cdk synth \
  --parameters FirehoseStreamName=<i>'your-delivery-stream-name'</i> \
  --parameters FirehosePrefix=<i>'your-s3-bucket-prefix'</i>
</pre>

### Schema validation with an AWS Lambda function

For example, let's validate schema of the record with an AWS Lambda function for the following sample data.

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

You can validate the schema of incomming records with the data transform Lambda function.
For example, you are going to check if all keys are supposed not to have null values with the AWS Lambda function in Python like this:

```python

def check_schema(json_value):
  is_valid = True
  for v in json_value.values():
    if not v:
       is_valid = False
       break
    elif type(v) == type({}):
       is_valid = check_schema(v)
  return is_valid

def lambda_handler(firehose_records_input, context):
  # Create return value.
  firehose_records_output = {'records': []}

  # Create result object.
  # Go through records and process them
  for firehose_record_input in firehose_records_input['records']:
    # Get user payload
    payload = base64.b64decode(firehose_record_input['data'])
    json_value = json.loads(payload)

    # check if schema is valid
    is_valid = check_schema(json_value)

    # Create output Firehose record and add modified payload and record ID to it.
    firehose_record_output = {
      'recordId': firehose_record_input['recordId'],
      'data': firehose_record_input['data'],
      # 'ProcessFailed' record will be put into error bucket in S3
      'result': 'Ok' if is_valid else 'ProcessingFailed'
    }

    # Add the record to the list of output records.
    firehose_records_output['records'].append(firehose_record_output)

  # At the end return processed records
  return firehose_records_output
```

Now you can create kinesis data firehose like this:

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
(.venv) $ cdk synth \
  --parameters FirehoseStreamName='PUT-S3-DataTransform' \
  --parameters FirehosePrefix='json-data/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/'
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy \
  --parameters FirehoseStreamName=<i>'your-delivery-stream-name'</i> \
  --parameters FirehosePrefix=<i>'your-s3-bucket-prefix'</i>
</pre>

For example,
<pre>
(.venv) $ cdk deploy \
  --parameters FirehoseStreamName='PUT-S3-DataTransform' \
  --parameters FirehosePrefix='json-data/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/'
</pre>

### Verify

If you want to generate sample data and verify it is being processed and stored as follows: `Direct Put -> Kinesis Data Firehose -> S3`, <br/>
Run `gen_fake_firehose_data.py` script on the EC2 instance by entering the following command:

<pre>
(.venv) $ cd ..
(.venv) $ ls src/main/python/
gen_fake_firehose_data.py
(.venv) $ pip install boto3 Faker # pip install -r requirements.txt
(.venv) $ python src/utils/gen_fake_firehose_data.py --stream-name <i>'your-delivery-stream-name'</i> --max-count -1
</pre>

If you would like to know more about the usage of this command, you can type

<pre>
(.venv) $ python src/utils/gen_fake_firehose_data.py --help
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
