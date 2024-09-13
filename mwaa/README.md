
# Amazon Managed Workflows for Apache Airflow (MWAA) CDK Python project!

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
(.venv) $ pip install -r requirements.txt
```

## Before you deploy
Before you deploy this project, you should create an Amazon S3 bucket to store your
Apache Airflow Directed Acyclic Graphs (DAGs), custom plugins in a plugins.zip file,
and Python dependencies in a requirements.txt file.
Check this [Create an Amazon S3 bucket for Amazon MWAA](https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-s3-bucket.html)

<pre>
$ aws s3 mb s3://<i>your-s3-bucket-for-airflow-dag-code</i> --region <i>region-name</i>
$ aws s3api put-public-access-block --bucket <i>your-s3-bucket-for-airflow-dag-code</i> --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
$ aws s3api put-bucket-versioning --bucket <i>your-s3-bucket-for-airflow-dag-code</i> --versioning-configuration Status=Enabled
$ aws s3api put-object --bucket <i>your-s3-bucket-for-airflow-dag-code</i> --key dags/
$ aws s3api put-object --bucket <i>your-s3-bucket-for-airflow-dag-code</i> --key requirements/requirements.txt
</pre>

## Deploy
At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk -c s3_bucket_for_dag_code='<i>your-s3-bucket-for-airflow-dag-code</i>' \
              -c airflow_env_name='<i>your-airflow-env-name</i>' \
              synth --all
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk -c s3_bucket_for_dag_code='<i>your-s3-bucket-for-airflow-dag-code</i>' \
              -c airflow_env_name='<i>your-airflow-env-name</i>' \
              deploy --all
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Clean Up

Delete the CloudFormation stack by running the below command.

<pre>
(.venv) $ cdk destroy --force --all
</pre>

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

## References

 * [Amazon MWAA - Networking](https://docs.aws.amazon.com/mwaa/latest/userguide/networking.html)
 * [Apache Airflow versions on Amazon Managed Workflows for Apache Airflow](https://docs.aws.amazon.com/mwaa/latest/userguide/airflow-versions.html)
 * [Amazon MWAA frequently asked questions](https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-faqs.html)
 * [Troubleshooting Amazon Managed Workflows for Apache Airflow](https://docs.aws.amazon.com/mwaa/latest/userguide/troubleshooting.html)

## Learn more

 * [Tutorials for Amazon Managed Workflows for Apache Airflow](https://docs.aws.amazon.com/mwaa/latest/userguide/tutorials.html)
 * [Best practices for Amazon Managed Workflows for Apache Airflow](https://docs.aws.amazon.com/mwaa/latest/userguide/best-practices.html)
 * [Code examples for Amazon Managed Workflows for Apache Airflow](https://docs.aws.amazon.com/mwaa/latest/userguide/sample-code.html)
 * [Orchestrate AWS Glue DataBrew jobs using Amazon Managed Workflows for Apache Airflow](https://aws.amazon.com/blogs/big-data/orchestrate-aws-glue-databrew-jobs-using-amazon-managed-workflows-for-apache-airflow/)
   * Code Repository: [aws-mwaa-glue-databrew-nytaxi](https://github.com/ksmin23/aws-mwaa-glue-databrew-nytaxi)
 * [Amazon MWAA for Analytics Workshop](https://amazon-mwaa-for-analytics.workshop.aws/en/)
 * [Get started with Amazon Managed Workflows for Apache Airflow \(MWAA\)](https://docs.aws.amazon.com/mwaa/latest/userguide/get-started.html)

## Tips
  * To update `requirements.txt`, run the commands like this:
    ```
    $ obj_version=$(aws s3api list-object-versions --bucket <i>your-s3-bucket-for-airflow-requirements</i> --prefix 'requirements/requirements.txt' | jq '.Versions[0].VersionId' | sed -e "s/\"//g")
    $ echo ${obj_version}
    $ aws mwaa update-environment \
        --region <i>region-name</i> \
        --name <i>your-airflow-environment</i> \
        --requirements-s3-object-version ${obj_version}
    ```
  * sample `requirements.txt`
    - :information_source: **MUST CHECK** python package version at here: [https://raw.githubusercontent.com/apache/airflow/constraints-2.0.2/constraints-3.7.txt](https://raw.githubusercontent.com/apache/airflow/constraints-2.0.2/constraints-3.7.txt)
    ```
    apache-airflow-providers-elasticsearch==1.0.3
    apache-airflow-providers-redis==1.0.1
    apache-airflow-providers-google==2.2.0
    apache-airflow-providers-mysql==1.1.0
    ```

Enjoy!

