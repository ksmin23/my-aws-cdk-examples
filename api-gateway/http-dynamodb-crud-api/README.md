
# CRUD HTTP API Gateway for DynamoDB CDK Python project!

![dynamodb_crud_http_api](./dynamodb_crud_http_api.svg)

This is a CRUD API project using Lambda and DynamoDB for CDK development with Python.
In this project, you create a serverless API that creates, reads, updates, and deletes items from a DynamoDB table.

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

Before synthesizing the CloudFormation, you should set approperly the cdk context configuration file, `cdk.context.json`.

For example:

```
{
  "vpc_name": "default",
  "dynamodb": {
    "table_name": "http-crud-tutorial-items",
    "partition_key": "id",
    "time_to_live_attribute": "ttl"
  }
}
```

At this point you can now synthesize the CloudFormation template for this code.

```
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all
```

Use `cdk deploy` command to create the stack shown above,

```
(.venv) $ cdk deploy --all
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Test

#### To create or update an item

Use the following command to create or update an item. The command includes a request body with the item's ID, price, and name.

```
curl -X "PUT" -H "Content-Type: application/json" -d "{\"id\": \"123\", \"price\": 12345, \"name\": \"myitem\"}" https://abcdef123.execute-api.us-east-1.amazonaws.com/items
```

HTTP Request Event Example for Lambda function:

```
{
  version: '2.0',
  routeKey: 'PUT /items',
  rawPath: '/items',
  rawQueryString: '',
  headers: {
    accept: '*/*',
    'content-length': '47',
    'content-type': 'application/json',
    host: 'abcdef123.execute-api.us-east-1.amazonaws.com',
    'user-agent': 'curl/7.87.0',
    'x-amzn-trace-id': 'Root=1-64562dc6-7752b044606e259624b293e4',
    'x-forwarded-for': '172.31.171.253',
    'x-forwarded-port': '443',
    'x-forwarded-proto': 'https'
  },
  requestContext: {
    accountId: '123456789012',
    apiId: 'abcdef123',
    domainName: 'abcdef123.execute-api.us-east-1.amazonaws.com',
    domainPrefix: 'abcdef123',
    http: {
      method: 'PUT',
      path: '/items',
      protocol: 'HTTP/1.1',
      sourceIp: '172.31.171.253',
      userAgent: 'curl/7.87.0'
    },
    requestId: 'EfwW_jHaoAMEJXw=',
    routeKey: 'PUT /items',
    stage: '$default',
    time: '06/May/2023:10:36:54 +0000',
    timeEpoch: 1683369414051
  },
  body: '{"id": "123", "price": 12345, "name": "myitem"}',
  isBase64Encoded: false
}
```

#### To get all items

Use the following command to list all items.

```
curl https://abcdef123.execute-api.us-east-1.amazonaws.com/items
```

HTTP Request Event Example for Lambda function:

```
{
  version: '2.0',
  routeKey: 'GET /items',
  rawPath: '/items',
  rawQueryString: '',
  headers: {
    accept: '*/*',
    'content-length': '0',
    host: 'abcdef123.execute-api.us-east-1.amazonaws.com',
    'user-agent': 'curl/7.87.0',
    'x-amzn-trace-id': 'Root=1-645625ef-1800537b7453cfdf4f7fe05f',
    'x-forwarded-for': '172.31.171.253',
    'x-forwarded-port': '443',
    'x-forwarded-proto': 'https'
  },
  requestContext: {
    accountId: '123456789012',
    apiId: 'abcdef123',
    domainName: 'abcdef123.execute-api.us-east-1.amazonaws.com',
    domainPrefix: 'abcdef123',
    http: {
      method: 'GET',
      path: '/items',
      protocol: 'HTTP/1.1',
      sourceIp: '172.31.171.253',
      userAgent: 'curl/7.87.0'
    },
    requestId: 'EfrdZjP6IAMEJgw=',
    routeKey: 'GET /items',
    stage: '$default',
    time: '06/May/2023:10:03:27 +0000',
    timeEpoch: 1683367407068
  },
  isBase64Encoded: false
}
```

#### To get an item

Use the following command to get an item by its ID.

```
curl https://abcdef123.execute-api.us-east-1.amazonaws.com/items/123
```

HTTP Request Event Example for Lambda function:

```
{
  version: '2.0',
  routeKey: 'GET /items/{id}',
  rawPath: '/items/123',
  rawQueryString: '',
  headers: {
    accept: '*/*',
    'content-length': '0',
    host: 'abcdef123.execute-api.us-east-1.amazonaws.com',
    'user-agent': 'curl/7.87.0',
    'x-amzn-trace-id': 'Root=1-64562ee6-0fcaba570c17f78b7e3a9006',
    'x-forwarded-for': '172.31.171.253',
    'x-forwarded-port': '443',
    'x-forwarded-proto': 'https'
  },
  requestContext: {
    accountId: '123456789012',
    apiId: 'abcdef123',
    domainName: 'abcdef123.execute-api.us-east-1.amazonaws.com',
    domainPrefix: 'abcdef123',
    http: {
      method: 'GET',
      path: '/items/123',
      protocol: 'HTTP/1.1',
      sourceIp: '172.31.171.253',
      userAgent: 'curl/7.87.0'
    },
    requestId: 'EfxEEgdMIAMES7w=',
    routeKey: 'GET /items/{id}',
    stage: '$default',
    time: '06/May/2023:10:41:42 +0000',
    timeEpoch: 1683369702592
  },
  pathParameters: { id: '123' },
  isBase64Encoded: false
}
```

#### To delete an item

Use the following command to delete an item.

```
curl -X "DELETE" https://abcdef123.execute-api.us-east-1.amazonaws.com/items/123
```

HTTP Request Event Example for Lambda function:

```
{
  version: '2.0',
  routeKey: 'DELETE /items/{id}',
  rawPath: '/items/123',
  rawQueryString: '',
  headers: {
    accept: '*/*',
    'content-length': '0',
    host: 'abcdef123.execute-api.us-east-1.amazonaws.com',
    'user-agent': 'curl/7.87.0',
    'x-amzn-trace-id': 'Root=1-64562f8d-43d9def50321e9dd0f470f59',
    'x-forwarded-for': '172.31.171.253',
    'x-forwarded-port': '443',
    'x-forwarded-proto': 'https'
  },
  requestContext: {
    accountId: '123456789012',
    apiId: 'abcdef123',
    domainName: 'abcdef123.execute-api.us-east-1.amazonaws.com',
    domainPrefix: 'abcdef123',
    http: {
      method: 'DELETE',
      path: '/items/123',
      protocol: 'HTTP/1.1',
      sourceIp: '172.31.171.253',
      userAgent: 'curl/7.87.0'
    },
    requestId: 'EfxeOg2YIAMEJUw=',
    routeKey: 'DELETE /items/{id}',
    stage: '$default',
    time: '06/May/2023:10:44:29 +0000',
    timeEpoch: 1683369869936
  },
  pathParameters: { id: '123' },
  isBase64Encoded: false
}
```

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

## References

 * [Amazon API Gateway - Tutorial: Build a CRUD API with Lambda and DynamoDB](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-dynamo-db.html)
 * [Simple HTTP CRUD API for DynamoDB CDK Typescript Project in AWS CDK v1](https://github.com/aws-samples/simple-crud-api)
 * [Http API Example in AWS CDK Typescript (API Gateway V2)](https://bobbyhadz.com/blog/aws-cdk-http-api-apigateway-v2-example)
 * [Amazon API Gateway - Working with AWS Lambda proxy integrations for HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html)
 * [Amazon API Gateway - Working with HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html)
