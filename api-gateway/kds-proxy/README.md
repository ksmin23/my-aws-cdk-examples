
# Create a REST API as an Amazon Kinesis proxy in API Gateway

![apigw-kds-proxy-arch](./apigw-kds-proxy-arch.svg)

This is an Amazon Kinesis proxy project using API Gateway for CDK development with Python.

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
(.venv) $ cdk synth \
              -c vpc_name=default \
              --parameters SourceKinesisStreams='<i>your-kinesis-stream-name</i>'
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy --require-aproval never \
              -c vpc_name=default \
              --parameters SourceKinesisStreams='<i>your-kinesis-stream-name</i>'
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Examples

- `GET /streams` method to invoke `ListStreams` in Kinesis

  <pre>
  $ curl -X GET https://<i>your-api-gateway-id</i>.execute-api.us-east-1.amazonaws.com/v1/streams
  </pre>

  The response is:
  <pre>
  {
    "HasMoreStreams": false,
    "StreamNames": [
      "PUT-Firehose-aEhWz"
    ],
    "StreamSummaries": [
      {
        "StreamARN": "arn:aws:kinesis:us-east-1:123456789012:stream/PUT-Firehose-aEhWz",
        "StreamCreationTimestamp": 1661612556,
        "StreamModeDetails": {
          "StreamMode": "ON_DEMAND"
        },
        "StreamName": "PUT-Firehose-aEhWz",
        "StreamStatus": "ACTIVE"
      }
    ]
  }
  </pre>

- `GET /streams/{stream-name}` method to invoke `DescribeStream` in Kinesis

  <pre>
  $ curl -X GET https://<i>your-api-gateway-id</i>.execute-api.us-east-1.amazonaws.com/v1/streams/PUT-Firehose-aEhWz
  </pre>

  The response is:
  <pre>
  {
    "StreamDescription": {
      "EncryptionType": "KMS",
      "EnhancedMonitoring": [
        {
          "ShardLevelMetrics": []
        }
      ],
      "HasMoreShards": false,
      "KeyId": "alias/aws/kinesis",
      "RetentionPeriodHours": 24,
      "Shards": [
        {
          "HashKeyRange": {
            "EndingHashKey": "340282366920938463463374607431768211455",
            "StartingHashKey": "0"
          },
          "SequenceNumberRange": {
            "StartingSequenceNumber": "49632740478318570836537313591685157894516301790768529410"
          },
          "ShardId": "shardId-000000000000"
        }
      ],
      "StreamARN": "arn:aws:kinesis:us-east-1:123456789012:stream/PUT-Firehose-aEhWz",
      "StreamCreationTimestamp": 1661612556,
      "StreamModeDetails": {
        "StreamMode": "ON_DEMAND"
      },
      "StreamName": "PUT-Firehose-aEhWz",
      "StreamStatus": "ACTIVE"
    }
  }
  </pre>

- `PUT /streams/{stream-name}/record` method to invoke `PutRecord` in Kinesis

  <pre>
  $ curl -X PUT https://<i>your-api-gateway-id</i>.execute-api.us-east-1.amazonaws.com/v1/streams/PUT-Firehose-aEhWz/record \
         -H 'Content-Type: application/json' \
         -d '{ "Data": "some data", "PartitionKey": "some key" }'
  </pre>

  The response is:
  <pre>
  {
    "EncryptionType": "KMS",
    "SequenceNumber": "49632757272385358984391127998703515973414866647712268290",
    "ShardId": "shardId-000000000000"
  }
  </pre>

- `PUT /streams/{stream-name}/records` method to invoke `PutRecords` in Kinesis

  <pre>
  $ curl -X PUT https://<i>your-api-gateway-id</i>.execute-api.us-east-1.amazonaws.com/v1/streams/PUT-Firehose-aEhWz/records \
         -H 'Content-Type: application/json' \
         -d '{"records":[{"data":"some data","partition-key":"some key"},{"data":"some other data","partition-key":"some key"}]}'
  </pre>

  The response is:
  <pre>
  {
    "EncryptionType": "KMS",
    "FailedRecordCount": 0,
    "Records": [
      {
        "SequenceNumber": "49632757272385358984391128069035193381135165118304223234",
        "ShardId": "shardId-000000000000"
      },
      {
        "SequenceNumber": "49632757272385358984391128069037611232774394376653635586",
        "ShardId": "shardId-000000000000"
      }
    ]
  }
  </pre>

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

 * [Tutorial: Create a REST API as an Amazon Kinesis proxy in API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/integrating-api-with-aws-services-kinesis.html)
 * [Streaming Data Solution for Amazon Kinesis](https://aws.amazon.com/ko/solutions/implementations/aws-streaming-data-solution-for-amazon-kinesis/)
 * [Serverless Patterns Collection](https://serverlessland.com/patterns)
 * [aws-samples/serverless-patterns](https://github.com/aws-samples/serverless-patterns)
 * [Curl Cookbook](https://catonmat.net/cookbooks/curl)

## Trouble Shooting

  <pre>
  { "message": "Missing Authentication Token" }
  </pre>

 * [How do I troubleshoot API Gateway REST API endpoint 403 "Missing Authentication Token" errors?](https://aws.amazon.com/premiumsupport/knowledge-center/api-gateway-authentication-token-errors/)
 * [API Gateway permissions model for invoking an API](https://docs.aws.amazon.com/apigateway/latest/developerguide/permissions.html#api-gateway-control-access-iam-permissions-model-for-calling-api)

