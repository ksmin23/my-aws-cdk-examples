
# Knowledge Bases for Amazon Bedrock CDK Python project!

This is a Knowledge Base for Amazon Bedrock project for CDK development with Python.

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

Before deployment, you need to make sure `docker daemon` is running.
Otherwise you will encounter the following errors:

```
ERROR: Cannot connect to the Docker daemon at unix://$HOME/.docker/run/docker.sock. Is the docker daemon running?
jsii.errors.JavaScriptError:
  Error: docker exited with status 1
```

### Set up `cdk.context.json`

Then, you should set approperly the cdk context configuration file, `cdk.context.json`.

For example,

<pre>
{
  "knowledge_base_data_source_name": "kb-data-source"
}
</pre>
:warning: It would be better **NOT TO USE** `metadata` for `metadata_field` in OpenSearch serverless field mapping. The popular LLM application frameworks like [LangChain](https://www.langchain.com/), [LlamaIndex](https://www.llamaindex.ai/) use `metadata` with data type other than `text` for OpenSearch field mapping. So to avoid conflicts when using the popular LLM frameworks, be careful to use `metadata` field name.

## Deploy

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) cdk deploy
</pre>

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

## References

 * [AWS Generative AI CDK Constructs](https://awslabs.github.io/generative-ai-cdk-constructs/)
 * [Announcing Generative AI CDK Constructs (2024-01-31)](https://aws.amazon.com/blogs/devops/announcing-generative-ai-cdk-constructs/)
 * [(Video) AWS re:Invent 2023 - Use RAG to improve responses in generative AI applications (AIM336)](https://youtu.be/N0tlOXZwrSs?t=1659)
 * [Knowledge Bases now delivers fully managed RAG experience in Amazon Bedrock (2023-11-28)](https://aws.amazon.com/blogs/aws/knowledge-bases-now-delivers-fully-managed-rag-experience-in-amazon-bedrock/)
 * [Knowledge base for Amazon Bedrock Developer Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
 * [LangChain - AmazonKnowledgeBasesRetriever](https://python.langchain.com/docs/integrations/retrievers/bedrock)
 * [Building with Amazon Bedrock and LangChain](https://catalog.workshops.aws/building-with-amazon-bedrock/en-US) - Hands-on labs using [LangChain](https://github.com/langchain-ai/langchain) to build generative AI prototypes with Amazon Bedrock.
 * [Amazon Bedrock Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/a4bdb007-5600-4368-81c5-ff5b4154f518/en-US) - Hands-on labs using Amazon Bedrock APIs, SDKs, and open-source software, such as LangChain and FAISS, to implement the most common Generative AI usage patterns (e.g., summarizing text, answering questions, building chatbots, creating images, and generating code).

