
# Custom Resources CDK Python project!

This is a Custom Resource example for CDK development with Python.

In this project, we will deploy SageMaker JumpStart model into SageMaker Endpoint.

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
(.venv) $ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
(.venv) $ pip install -r requirements.txt
```

### Upload Lambda Layer code

Before deployment, you should uplad zipped code files to s3 like this example:

> :warning: **Important**: Replace `lambda-layer-resources` with your s3 bucket name for lambda layer zipped code.
> :warning: To create a bucket outside of the `us-east-1` region, `aws s3api create-bucket` command requires the appropriate **LocationConstraint** to be specified in order to create the bucket in the desired region. For more information, see these [examples](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/s3api/create-bucket.html#examples).

> :warning: Make sure you have **Docker** installed.

<pre>
(.venv) $ aws s3api create-bucket --bucket lambda-layer-resources --region <i>us-east-1</i>
(.venv) $ cat <<EOF>requirements-lambda_layer.txt
 > sagemaker==2.188
 > cfnresponse==1.1.2
 > urllib3==1.26.16
 > EOF
(.venv) $ docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.10" /bin/sh -c "pip install -r requirements-lambda_layer.txt -t python/lib/python3.10/site-packages/; exit"
(.venv) $ zip -r sagemaker-python-sdk-lib.zip python > /dev/null
(.venv) $ aws s3 cp sagemaker-python-sdk-lib.zip s3://lambda-layer-resources/pylambda-layer/
</pre>

For more information about how to create a package for Amazon Lambda Layer, see [here](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-simulated-docker/).

### Deploy

Before to synthesize the CloudFormation template for this code, you should update `cdk.context.json` file.<br/>
In particular, you need to fill the s3 location of the previously created lambda lay codes.

For example,
<pre>
{
  "lambda_layer_lib_s3_path": "s3://lambda-layer-resources/pylambda-layer/sagemaker-python-sdk-lib.zip",
  "sagemaker_jumpstart_model_info": {
    "model_id": "meta-textgeneration-llama-2-7b-f",
    "endpoint_name": "meta-textgen-llama-2-7b-f"
  }
}
</pre>

Now you are ready to synthesize the CloudFormation template for this code.

```
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all
```

Use `cdk deploy` command to create the stack shown above.

```
(.venv) $ cdk deploy --require-approval never --all
```

Or, we can provision each CDK stack one at a time like this:

#### Step 1: List all CDK Stacks

```
(.venv) $ cdk list
SageMakerPySDKLambdaLayerStack
SageMakerEndpointIAMRoleStack
SMJumpStartModelDeployLambdaStack
SMJumpStartModelEndpointStack
```

#### Step 2: Create Amazon Lambda Layer for Amazon Lambda Function

```
(.venv) $ cdk deploy --require-approval never SageMakerPySDKLambdaLayerStack
```

#### Step 3: Create IAM Role for SageMaker Endpoint

```
(.venv) $ cdk deploy --require-approval never SageMakerEndpointIAMRoleStack
```

#### Step 2: Create Amazon Lambda Function for Custome Resource Provider

```
(.venv) $ cdk deploy --require-approval never SMJumpStartModelDeployLambdaStack
```

#### Step 4: Deploy SageMaker JumpStart Model

```
(.venv) $ cdk deploy --require-approval never SMJumpStartModelEndpointStack
```

> :warning: Deploying SageMaker JumpStart Model (i.e., **Step 4**) requires about `5~15` minutes. Therefore, wait for about a few minutes after launching the `SMJumpStartModelEndpointStack` to use SageMaker Endpoint.

> :information_source: To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

Once all CDK stacks have been successfully created, we can use SageMaker Endpoint.

## Test

For example, we can test SageMaker Endpoint that `meta-textgeneration-llama-2-7b-f` is deployed by running the following code in SageMaker Studio.

```python
import base64
import json
import boto3

region = boto3.session.Session().region_name

def query_endpoint(payload, endpoint_name=None, region_name='us-east-1'):
    client = boto3.client("sagemaker-runtime", region_name=region_name)
    response = client.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="application/json",
        Body=json.dumps(payload),
        CustomAttributes="accept_eula=true", # eula: End User Licence Agreement
    )
    response = response["Body"].read().decode("utf8")
    response = json.loads(response)
    return response

#TODO: Should create a right payload based on your ML model
payload = {
    "inputs": [
        [
            {"role": "system", "content": "Always answer with Haiku"},
            {"role": "user", "content": "I am going to Paris, what should I see?"}
        ]
    ],
    "parameters": {"max_new_tokens": 256, "top_p": 0.9, "temperature": 0.6}
}

TEXT2TEXT_ENDPOINT_NAME = "meta-textgen-llama-2-7b-f" #TODO: Replace your endpoint name
result = query_endpoint(payload, TEXT2TEXT_ENDPOINT_NAME)[0]
print(result)
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

  * [SageMaker Python SDK - Deploy a Pre-Trained Model Directly to a SageMaker Endpoint](https://sagemaker.readthedocs.io/en/stable/overview.html#deploy-a-pre-trained-model-directly-to-a-sagemaker-endpoint)
  * [Use proprietary foundation models from Amazon SageMaker JumpStart in Amazon SageMaker Studio (2023-06-27)](https://aws.amazon.com/blogs/machine-learning/use-proprietary-foundation-models-from-amazon-sagemaker-jumpstart-in-amazon-sagemaker-studio/)
  * [AWS CDK TypeScript Example - Custom Resource](https://github.com/aws-samples/aws-cdk-examples/tree/master/typescript/custom-resource)
  * [How to create a Lambda layer using a simulated Lambda environment with Docker](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-simulated-docker/)
    ```
    $ cat <<EOF>requirements-lambda_layer.txt
    > sagemaker==2.188
    > cfnresponse==1.1.2
    > urllib3==1.26.16
    > EOF

    $ docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.10" /bin/sh -c "pip install -r requirements-lambda_layer.txt -t python/lib/python3.10/site-packages/; exit"

    $ zip -r sagemaker-python-sdk-lib.zip python > /dev/null

    $ aws s3 mb s3://my-bucket-for-lambda-layer-packages

    $ aws s3 cp sagemaker-python-sdk-lib.zip s3://my-bucket-for-lambda-layer-packages/pylambda-layer/
    ```

## Troubleshooting

  * [(AWS re:Post) Stack deletion stuck as DELETE_IN_PROGRESS](https://repost.aws/questions/QUoEeYfGTeQHSyJSrIDymAoQ/stack-deletion-stuck-as-delete-in-progress)
  * [(Video) How do I delete an AWS Lambda-backed custom resource that’s stuck deleting in AWS CloudFormation?](https://youtu.be/hlJkMoCxR-I?si=NgaNwr9vH15daUBz)
  * [(Stack Overflow)"cannot import name 'DEFAULT_CIPHERS' from 'urllib3.util.ssl_'" on AWS Lambda using a layer](https://stackoverflow.com/questions/76414514/cannot-import-name-default-ciphers-from-urllib3-util-ssl-on-aws-lambda-us)
    * **Error message**:
      ```
      cannot import name 'DEFAULT_CIPHERS' from 'urllib3.util.ssl_' (/opt/python/lib/python3.10/site-packages/urllib3/util/ssl_.py
      ```
    * **Solution**: You’ll need to explicitly pin to `urllib3<2` in your project to ensure `urllib3 2.0` isn’t brought into your environment.
      ```
      urllib3<2
      ```
