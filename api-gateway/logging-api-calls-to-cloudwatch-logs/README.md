
# Logging Amazon API Gateway API Calls to Amazon Kinesis Data Firehose using CloudWatch Logs Subscription Filters

![logging-api-calls-to-cloudwatch-logs](./logging-api-calls-to-cloudwatch-logs.svg)

This is a CDK Python project for logging API calls to Amazon Kinesis Data Firehose using CloudWatch Logs subscription filters.

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
(.venv) $ cdk synth -c firehose_name=<i>{your-delivery-stream-name}</i> --all
</pre>

:warning: The name of your Kinesis Data Firehose delivery stream **MUST NOT** start with `amazon-apigateway-` prefix.
If your delivery stream name had `amazon-apigateway-` prefix, you would encounter the following error like this during deployment:
<pre>
Resource handler returned message: "Could not deliver test message to specified Firehose stream. Check if the given Firehose stream is in ACTIVE state. (Service: CloudWatchLogs, Status Code: 400, Request ID: aaaa7f10-a5d6-44d5-8191-dba9f27d36f3)" (RequestToken: bb4b2fc5-26cd-de7b-a7d9-8653c44f8642, HandlerErrorCode: InternalFailure)
</pre>

Use `cdk deploy` command to create the stack shown above,

<pre>
(.venv) $ cdk deploy -c firehose_name=<i>{your-delivery-stream-name}</i> --all
</pre>

After deployment, you can find out the cloud watch log subscription filters with Amazon Kinesis Data Firehose by running the following instructions.

<pre>
$ CW_LOG_GROUP_NAME=$(aws cloudformation describe-stacks --stack-name LoggingApiCallsToCloudwatchLogsStack  | jq -r '.Stacks[0].Outputs | map(select(.OutputKey == "RestApiAccessLogGroupName")) | .[0].OutputValue')
$ aws logs describe-subscription-filters --log-group-name ${CW_LOG_GROUP_NAME}
{
    "subscriptionFilters": [
        {
            "filterName": "LoggingApiCallsToCloudwatchLogsStack-CWLSubscriptionFilter-Zi6qt8IvfIJV",
            "logGroupName": "LoggingApiCallsToCloudwatchLogsStack-RandomGenApiLogs96EBA3FC-VV1l7d2OJqLV",
            "filterPattern": "",
            "destinationArn": "arn:aws:firehose:us-east-1:123456789012:deliverystream/PUT-S3-vvMmG",
            "roleArn": "arn:aws:iam::123456789012:role/CWLtoKinesisFirehoseRole",
            "distribution": "ByLogStream",
            "creationTime": 1670315295923
        }
    ]
}
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

## Run Test

1. Invoke REST API method
   <pre>
   $ curl -X GET 'https://<i>{your-api-gateway-id}</i>.execute-api.<i>{region}</i>.amazonaws.com/prod/random/strings?len=7'
   </pre>

   The response is:
   <pre>
   ["weBJDKv"]
   </pre>

2. Generate test requests and run them.
   <pre>
   $ cat <&lt;EOF > run_test.sh
   > curl 'https://<i>{your-api-gateway-id}</i>.execute-api.<i>{region}</i>.amazonaws.com/prod/random/strings?len=7'
   > curl 'https://<i>{your-api-gateway-id}</i>.execute-api.<i>{region}</i>.amazonaws.com/prod/random/strings?chars=letters'
   > curl 'https://<i>{your-api-gateway-id}</i>.execute-api.<i>{region}</i>.amazonaws.com/prod/random/strings?chars=letters&len=15'
   > curl 'https://<i>{your-api-gateway-id}</i>.execute-api.<i>{region}</i>.amazonaws.com/prod/random/strings?chars=lowercase&len=15'
   > curl 'https://<i>{your-api-gateway-id}</i>.execute-api.<i>{region}</i>.amazonaws.com/prod/random/strings?chars=uppercase&len=5'
   > curl 'https://<i>{your-api-gateway-id}</i>.execute-api.<i>{region}</i>.amazonaws.com/prod/random/strings?chars=digits&len=7'
   > curl 'https://<i>{your-api-gateway-id}</i>.execute-api.<i>{region}</i>.amazonaws.com/prod/random/strings?chars=digits&len=17'
   > curl 'https://<i>{your-api-gateway-id}</i>.execute-api.<i>{region}</i>.amazonaws.com/prod/random/strings?len=3'
   > curl 'https://<i>{your-api-gateway-id}</i>.execute-api.<i>{region}</i>.amazonaws.com/prod/random/strings?chars=letters&len=9'
   > curl 'https://<i>{your-api-gateway-id}</i>.execute-api.<i>{region}</i>.amazonaws.com/prod/random/strings?len=17'
   > EOF
   $ bash ./run_test.sh
   </pre>

3. Check the access logs in S3

   After `5~10` minutes, you can see that the cloud watch logs have been delivered by Kinesis Data Firehose to S3 and stored in a folder structure by year, month, day, and hour.
   ![amazon-apigatewy-access-log-in-s3](./amazon-apigatewy-access-log-in-s3.png)

   The data in the Amazon S3 object is compressed with the gzip format. When you examine the raw data, you would see one of the following types of cloud watch logs:

   * Control Message
      <pre>
      {
         "messageType": "CONTROL_MESSAGE",
         "owner": "CloudwatchLogs",
         "logGroup": "",
         "logStream": "",
         "subscriptionFilters": [],
         "logEvents": [
            {
               "id": "",
               "timestamp": 1670315295923,
               "message": "CWL CONTROL MESSAGE: Checking health of destination Firehose."
            }
         ]
      }
      </pre>

   * Data Message

      <pre>
      {
         "messageType": "DATA_MESSAGE",
         "owner": "819320734790",
         "logGroup": "LoggingApiCallsToCloudwatchLogsStack-RandomGenApiLogs96EBA3FC-VV1l7d2OJqLV",
         "logStream": "a5f69e5c7656d84117661e8a24b04807",
         "subscriptionFilters": [
            "LoggingApiCallsToCloudwatchLogsStack-CWLSubscriptionFilter-Zi6qt8IvfIJV"
         ],
         "logEvents": [
            {
               "id": "37249425165417151864519688057747871138717457702689112064",
               "timestamp": 1670321993001,
               "message": "{\"requestId\": \"65401bed-607a-4b27-a33f-f1f5c811b1d2\", \"ip\": \"124.17.254.27\", \"user\": \"-\", \"requestTime\": 1670321993001, \"httpMethod\": \"GET\", \"resourcePath\": \"/random/strings\", \"status\": 200, \"protocol\": \"HTTP/1.1\", \"responseLength\": 11}\n"
            }
         ]
      }
      </pre>
   :information_source: The api access logs are included in the `logEvents` attribute as string data type.

## References

 * [Setting up CloudWatch logging for a REST API in API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html)
 * [Using CloudWatch Logs subscription filters with Amazon Kinesis Data Firehose](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/SubscriptionFilters.html#FirehoseExample)
 * [Curl Cookbook](https://catonmat.net/cookbooks/curl)

