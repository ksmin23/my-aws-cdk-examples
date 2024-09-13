
# Ingesting data from Kinesis Data Streams to S3 through Kinesis Data Firehose

![kinesis_streams_to_firehose_to_s3](./kinesis_streams_to_firehose_to_s3.svg)

This is a kinesis data streams project for Python development with CDK.

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
  --parameters KinesisStreamName=<i>'your-kinesis-data-stream-name'</i> \
  --parameters FirehoseStreamName=<i>'your-delivery-stream-name'</i> \
  --parameters FirehosePrefix=<i>'your-s3-bucket-prefix'</i>
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy --all \
  --parameters KinesisStreamName=<i>'your-kinesis-data-stream-name'</i> \
  --parameters FirehoseStreamName=<i>'your-delivery-stream-name'</i> \
  --parameters FirehosePrefix=<i>'your-s3-bucket-prefix'</i>
</pre>

### Verify

If you want to generate sample data and verify it is being processed and stored as follows: `Kinesis Data Streams -> Kinesis Data Firehose -> S3`, <br/>
Run `gen_fake_kinesis_stream_data.py` script on the EC2 instance by entering the following command:

<pre>
(.venv) $ cd ..
(.venv) $ ls src/main/python/
gen_fake_kinesis_stream_data.py
(.venv) $ pip install boto3 Faker # pip install -r requirements-dev.txt
(.venv) $ python src/main/python/gen_fake_kinesis_stream_data.py --stream-name <i>'your-kinesis-stream-name'</i> --max-count -1
</pre>

If you would like to know more about the usage of this command, you can type

<pre>
(.venv) $ python src/main/python/gen_fake_kinesis_stream_data.py --help
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

Enjoy!
