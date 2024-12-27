
# Access RDS database using Network Load Balancer (NLB)

![nlb_for_aurora_mysql-arch](./nlb_for_aurora_mysql-arch.svg)

This is a CDK Python project to access Amazon RDS using Network Load Balancer.

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

Before synthesizing the CloudFormation, you should set approperly the cdk context configuration file, `cdk.context.json`.

For example:

<pre>
{
  "db_cluster_name": "demo"
}
</pre>

At this point you can now synthesize the CloudFormation template for this code.

```
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all
```

Now we will be able to deploy all the CDK stacks at once like this:

```
(.venv) $ cdk deploy --require-approval never --all
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

 * [(AWS Blog) Replicate changes from databases to Apache Iceberg tables using Amazon Data Firehose (in preview)](https://aws.amazon.com/blogs/aws/replicate-changes-from-databases-to-apache-iceberg-tables-using-amazon-data-firehose/)
 * [(AWS Blog) Access Amazon RDS across VPCs using AWS PrivateLink and Network Load Balancer](https://aws.amazon.com/blogs/database/access-amazon-rds-across-vpcs-using-aws-privatelink-and-network-load-balancer/)
 * [(GitHub) Access Amazon RDS across VPCs using AWS PrivateLink and Network Load Balancer](https://github.com/aws-samples/amazon-rds-crossaccount-access/)
 * [AWS: Access RDS database using PrivateLink from another account (2022-03-04)](https://blog.andreev.it/2022/03/aws-access-rds-database-using-privatelink-from-another-account/)
 * [Setting Up AWS PrivateLink for Amazon RDS Access Between VPCs: A Step-by-Step Guide (2023-08-09)](https://medium.com/@anirban.ch.it/a-step-by-step-approach-to-setup-aws-privatelink-for-amazon-rds-across-vpcs-2ed69fc33f02)
