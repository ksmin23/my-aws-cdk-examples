
# CDK Python project for Kinesis Data Analytics application to Replicate Data from One MSK Cluster to Another in a VPC

## Prerequisites

Before create Kinesis Data Analytics for Flink Application, you need to finish the following steps in [Tutorial: Using a Kinesis Data Analytics application to Replicate Data from One MSK Cluster to Another in a VPC](https://docs.aws.amazon.com/kinesisanalytics/latest/java/example-msk.html)
- [Create an Amazon VPC with an Amazon MSK cluster](https://docs.aws.amazon.com/kinesisanalytics/latest/java/example-msk.html#example-msk-createcluster)
- [Create the Application Code](https://docs.aws.amazon.com/kinesisanalytics/latest/java/example-msk.html#example-msk-code)
- [Upload the Apache Flink Streaming Java Code](https://docs.aws.amazon.com/kinesisanalytics/latest/java/example-msk.html#example-msk-upload)

### Using a Kinesis Data Analytics application to Replicate Data from One Topic in an MSK Cluster to Another in a VPC

![kda-flink-msk-replication](./kda-flink-msk-replication.svg)

This is a blank project for Python development with CDK.

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

First, open `cdk.context.json` and update it properly

```json
{
  "s3_bucket_name": "Your-S3-KDA-App-Code-Location",
  "s3_path_to_flink_app_code": "Your-KDA-App-Code-Path",
  "kda_flink_property_groups": [
    {
      "property_group_id": "KafkaSource",
      "property_map": {
        "topic": "Your-Kafka-Source-Topic",
        "bootstrap.servers": "Your-Kafka-Broker-Servers"
      }
    },
    {
      "property_group_id": "KafkaSink",
      "property_map": {
        "topic": "Your-Kafka-Sink-Topic",
        "bootstrap.servers": "Your-Kafka-Broker-Servers"
        "transaction.timeout.ms": 30000
      }
    }
  ]
}
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
$ export CDK_DEFAULT_REGION=$(aws configure get region)
$ cdk synth
```

Use cdk deploy command to create the stack shown above,

```
$ cdk deploy
```

After successfully delpoyment, go to [Kinesis Data Analytics applications Dashboard](https://console.aws.amazon.com/kinesisanalytics/home), and then select your Kinesis Data Analytics applications and update VPC connectivity, and then `Run` application.

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Clean Up

Delete the CloudFormation stack by running the below command.

```
(.venv) $ cdk destroy
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
