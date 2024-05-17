
# Knowledge Base for Amazon Bedrock using Amazon OpenSearch Serverless

This is a complete setup for automatic deployment of Knowledge Bases for Amazon Bedrock using Amazon OpenSearch Serverless as a vector store.

Following resources will get created and deployed:

- AWS IAM role
- Amazon Open Search Serverless Collection and Index
- Set up Data Source and Knowledge Base for Amazon Bedrock

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

## Prerequisites

### Amazon S3 Bucket for a data source for Knowledge Base

- You already have s3 bucket where your documents are stored.<br/>
  (e.g., `aws s3 mb s3://bedrock-kb-us-east-1-123456789012 --region us-east-1`)
- The documents must be in one of the formats listed in [here](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-ds.html).

### Prepare Python Packages for AWS Lambda Layer

Before synthesizing the CloudFormation, **you first create a python package to regisiter with AWS Lambda Layer.
Then you upload the python package into S3 (e.g., <i>s3-bucket-lambda-layer-lib</i>)**

For more information about how to create a python package for AWS Lambda Layer, see [References](#references).

### Set up `cdk.context.json`

Then, you should set approperly the cdk context configuration file, `cdk.context.json`.

For example,

<pre>
{
  "knowledge_base_for_bedrock": {
    "name": "kb-demo",
    "description": "knowledge base description",
    "knowledge_base_configuration": {
      "vector_knowledge_base_configuration": {
        "embedding_model_arn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
      }
    },
    "storage_configuration": {
      "opensearch_serverless_configuration": {
        "field_mapping": {
          "metadata_field": "metadata_field",
          "text_field": "text",
          "vector_field": "vector_field"
        },
        "vector_index_name": "embedding_vectors"
      }
    }
  },
  "knowledge_base_data_source_configuration": {
    "name": "kb-vector-db",
    "data_deletion_policy": "RETAIN",
    "description": "data source description",
    "s3_configuration": {
      "bucket_arn": "arn:aws:s3:::bedrock-kb-us-east-1-123456789012"
    },
    "chunking_configuration": {
      "chunking_strategy": "FIXED_SIZE",
      "fixed_size_chunking_configuration": {
        "max_tokens": 512,
        "overlap_percentage": 20
      }
    }
  },
  "opensearch_collection_name": "kb-vector-db",
  "lambda_layer_lib_s3_path": "s3://lambda-layer-resources/pylambda-layer/opensearch-py-sdk-lib.zip"
}
</pre>
:warning: It would be better **NOT TO USE** `metadata` for `metadata_field` in OpenSearch serverless field mapping. The popular LLM application frameworks like LangChain, LlamaIndex use `metadata` with data type other than `text` for OpenSearch field mapping. So to avoid conflicts when using the popular LLM frameworks, be careful to use `metadata` field name.

Now this point you can now synthesize the CloudFormation template for this code.

```
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
(.venv) $ cdk synth --all
```

Now you can deploy all the CDK stacks at once like this:

```
(.venv) $ cdk deploy --require-approval never --all
```

## Clean Up

Delete the CloudFormation stacks by running the below command.

```
(.venv) $ cdk destroy --all
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

 * [Amazon Bedrock Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/a4bdb007-5600-4368-81c5-ff5b4154f518/en-US) - Hands-on labs using Amazon Bedrock APIs, SDKs, and open-source software, such as LangChain and FAISS, to implement the most common Generative AI usage patterns (e.g., summarizing text, answering questions, building chatbots, creating images, and generating code).
 * [Building with Amazon Bedrock and LangChain](https://catalog.workshops.aws/building-with-amazon-bedrock/en-US) - Hands-on labs using [LangChain](https://github.com/langchain-ai/langchain) to build generative AI prototypes with Amazon Bedrock.
 * [Amazon Bedrock Samples](https://github.com/aws-samples/amazon-bedrock-samples) - Pre-built examples to help customers get started with the Amazon Bedrock service.
   * [Deploy e2e RAG solution (using Knowledgebases for Amazon Bedrock) via CloudFormation](https://github.com/aws-samples/amazon-bedrock-samples/tree/main/knowledge-bases/03-infra/e2e-rag-using-bedrock-kb-cfn)
 * [AWS Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html#configuration-layers-path)
   * How to create a python package to register with AWS Lambda layer (e.g., **elasticsearch**, **pytz**) on **Amazon Linux**

      :warning: **You should create the python package on Amazon Linux, otherwise create it using a simulated Lambda environment with Docker.**
      <pre>
      $ python3 -m venv opensearch-py-lib
      $ cd opensearch-py-lib
      $ source bin/activate
      (opensearch-py-lib) $ mkdir -p python_modules
      (opensearch-py-lib) $ pip install opensearch-py==2.3.1 cfnresponse==1.1.2 urllib3==1.26.18 -t python_modules
      (opensearch-py-lib) $ mv python_modules python
      (opensearch-py-lib) $ zip -r opensearch-py-lib.zip python/
      (opensearch-py-lib) $ aws s3 mb s3://my-bucket-for-lambda-layer-packages
      (opensearch-py-lib) $ aws s3 cp opensearch-py-lib.zip s3://my-bucket-for-lambda-layer-packages/var/
      (opensearch-py-lib) $ deactivate
      </pre>
   * [How to create a Lambda layer using a simulated Lambda environment with Docker](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-simulated-docker/)
      <pre>
      $ cat <<EOF > requirements.txt
      > opensearch-py==2.3.1
      > cfnresponse==1.1.2
      > urllib3==1.26.18
      > EOF
      $ docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.10" /bin/sh -c "pip install -r requirements.txt -t python/lib/python3.10/site-packages/; exit"
      $ zip -r opensearch-py-lib.zip python > /dev/null
      $ aws s3 mb s3://my-bucket-for-lambda-layer-packages
      $ aws s3 cp opensearch-py-lib.zip s3://my-bucket-for-lambda-layer-packages/var/
      </pre>