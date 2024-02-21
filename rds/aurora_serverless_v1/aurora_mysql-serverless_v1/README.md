
# Aurora MySQL Serverless v1 Cluster

![aurora_mysql-serverless_v1-cluster-arch](./aurora_mysql-serverless_v1-cluster-arch.svg)

This is a sample project for CDK development with Python.<br/>
This project shows how to create Aurora MySQL Serverless v1 cluster.

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

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth -c db_cluster_name=mysql --all
```

Use `cdk deploy` command to create the stack shown above.

```
$ cdk deploy -c db_cluster_name=mysql --require-approval never --all
```

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

## References

 * [Using Amazon Aurora Serverless v1](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless.html)
 * [Comparison of Aurora Serverless v2 and Aurora Serverless v1](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.upgrade.html#aurora-serverless.comparison)
 * [Using Aurora Serverless v2](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.html)
 * [Aurora Serverless v2 - Region and version availability](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.requirements.html#aurora-serverless-v2-Availability)
   <pre>
   aws rds describe-orderable-db-instance-options \
       --engine aurora-mysql \
       --db-instance-class db.serverless \
       --region <i>my_region</i> \
       --query 'OrderableDBInstanceOptions[].[EngineVersion]' \
       --output text
   </pre>
   <pre>
    aws rds describe-orderable-db-instance-options \
       --engine aurora-postgresql \
       --db-instance-class db.serverless \
       --region <i>my_region</i> \
       --query 'OrderableDBInstanceOptions[].[EngineVersion]' \
       --output text
   </pre>
 * [Managing Aurora Serverless v2](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2-administration.html)
 * [Performance and scaling for Aurora Serverless v2](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.setting-capacity.html)
 * [Evaluate Amazon Aurora Serverless v2 for your provisioned Aurora clusters (2023-03-07)](https://aws.amazon.com/blogs/database/evaluate-amazon-aurora-serverless-v2-for-your-provisioned-aurora-clusters/)
   <pre>
   <b>Instance size</b>
   Any database instance in an Aurora cluster with memory up to 256 GB can be replaced with a serverless instance.
   The minimum capacity for the instance depends on the existing provisioned instance’s resource usage.
   Keep in mind that if Global Database is in use or if Performance Insights is enabled, the minimum is recommended to be 2 or above.
   The maximum capacity for the instance may be set to the equivalent of the provisioned instance capacity if it’s able to meet your workload requirements.
   For example, if the CPU utilization for a db.r6g.4xlarge (128 GB) instance stays at 10% most times,
   then the minimum ACUs may be set at 6.5 ACUs (10% of 128 GB) and maximum may be set at 64 ACUs (64x2GB=128GB).
   </pre>
