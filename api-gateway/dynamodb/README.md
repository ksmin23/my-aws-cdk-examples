
# Amazon API Gateway to DynamoDB integration

![apigw-dynamodb-arch](./apigw-dynamodb-arch.svg)

This is an Amazon API Gateway to DynamoDB integration project for Python development with CDK.

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

#### DynamoDB Table Desecriptions

 * Comments: store comments for each page of your website.
    <pre>
    {
      "TableName": "Comments",
      "KeySchema": [
        {
          "AttributeName": "commentId",
          "KeyType": "HASH"
        }
      ],
      "AttributeDefinitions": [
        {
          "AttributeName": "commentId",
          "AttributeType": "S"
        },
        {
          "AttributeName": "pageId",
          "AttributeType": "S"
        }
      ],
      "GlobalSecondaryIndexes": [
        {
          "IndexName": "pageId-index",
          "KeySchema": [
            {
              "AttributeName": "pageId",
              "KeyType": "HASH"
            }
          ],
          "Projection": {
              "ProjectionType": "ALL"
          }
        }
      ]
    }
    </pre>

#### API Definitions

 * Post Comments
    <pre>
    Resource: /comments
    HTTP Method: POST
    HTTP Request Body:
    {
      "pageId":   "example-page-id",
      "userName": "ExampleUserName",
      "message":  "This is an example comment to be added."
    }
    </pre>

 * Get Comments
    <pre>
    Resource: /comments/{pageId}
    HTTP Method: GET
    </pre>

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

 * [Using Amazon API Gateway as a proxy for DynamoDB](https://aws.amazon.com/blogs/compute/using-amazon-api-gateway-as-a-proxy-for-dynamodb/)
 * [Amazon API Gateway REST API to DynamoDB](https://serverlessland.com/patterns/apigw-dynamodb)
 * [Amazon API Gateway mapping template and access logging variable reference](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html)
 * [Building fine-grained authorization using Amazon Cognito, API Gateway, and IAM](https://aws.amazon.com/ko/blogs/security/building-fine-grained-authorization-using-amazon-cognito-api-gateway-and-iam/)
 * [Curl Cookbook](https://catonmat.net/cookbooks/curl)
