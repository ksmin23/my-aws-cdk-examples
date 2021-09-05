
# Amazon Managed workflows for Apache Airflow (MWAA) CDK Python project!

![amazon-mwaa](./mwaa-arch.svg)

This is a sample project for Python development with CDK.

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

## Before you deploy
Before you deploy this project, you should create an Amazon S3 bucket to store your 
Apache Airflow Directed Acyclic Graphs (DAGs), custom plugins in a plugins.zip file, 
and Python dependencies in a requirements.txt file.
Check this [Create an Amazon S3 bucket for Amazon MWAA](https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-s3-bucket.html)

## Deploy
At this point you can now synthesize the CloudFormation template for this code.

<pre>
$ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
$ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
$ cdk -c s3_bucket_for_dag_code='<i>your-s3-bucket-for-airflow-dag-code</i>' synth
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
cdk -c s3_bucket_for_dag_code='<i>your-s3-bucket-for-airflow-dag-code</i>' deploy
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

## Learn more

 * [Orchestrate AWS Glue DataBrew jobs using Amazon Managed Workflows for Apache Airflow](https://aws.amazon.com/blogs/big-data/orchestrate-aws-glue-databrew-jobs-using-amazon-managed-workflows-for-apache-airflow/)
 * [Amazon MWAA for Analytics Workshop](https://amazon-mwaa-for-analytics.workshop.aws/en/)
 * [Get started with Amazon Managed Workflows for Apache Airflow \(MWAA\)](https://docs.aws.amazon.com/mwaa/latest/userguide/get-started.html)

Enjoy!

