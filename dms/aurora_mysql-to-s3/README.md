
# Migrating Data from Aurora MySQL to S3 with AWS DMS

![dms-mysql-to-s3-arch](./dms-mysql-to-s3-arch.svg)

This is a data pipeline project using AWS DMS for Python development with CDK.

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
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
(.venv) $ cdk synth \
              -c vpc_name=default \
              -c aws_secret_name='<i>secret-full-name</i>' \
              -c mysql_client_security_group_name='<i>mysql-client-security-group-name</i>' \
              --parameters SourceDatabaseName='<i>database-name</i>' \
              --parameters SourceTableName='<i>table-name</i>' \
              --parameters TargetS3BucketName='<i>target-s3-bucket</i>' \
              --parameters TargetS3BucketFolderName='<i>target-s3-prefix</i>'
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy \
              -c vpc_name=default \
              -c aws_secret_name='<i>secret-full-name</i>' \
              -c mysql_client_security_group_name='<i>mysql-client-security-group-name</i>' \
              --parameters SourceDatabaseName='<i>database-name</i>' \
              --parameters SourceTableName='<i>table-name</i>' \
              --parameters TargetS3BucketName='<i>target-s3-bucket</i>' \
              --parameters TargetS3BucketFolderName='<i>target-s3-prefix</i>'
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

Enjoy!


## Example

1. Start the DMS Replication task by replacing the ARN in below command.
   <pre>
   (.venv) $ aws dms start-replication-task --replication-task-arn <i>dms-task-arn</i> --region <i>region-name</i>
   </pre>
2. Create an Aurora MySQL cluster with enabling binary logs; Set the `binlog_format parameter` to `ROW` in the parameter group.
3. Connect to the Aurora cluster writer node.
   <pre>
   $ mysql -h <i>db-cluster-name</i>.cluster-<i>xxxxxxxxxxxx</i>.<i>region-name</i>.rds.amazonaws.com -uadmin -p
    Welcome to the MySQL monitor.  Commands end with ; or \g.
    Your MySQL connection id is 947748268
    Server version: 5.7.12-log MySQL Community Server (GPL)

    Copyright (c) 2000, 2020, Oracle and/or its affiliates. All rights reserved.

    Oracle is a registered trademark of Oracle Corporation and/or its
    affiliates. Other names may be trademarks of their respective
    owners.

    Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

    mysql>
   </pre>
3. At SQL prompt run the below command to confirm that binary logging is enabled:
   <pre>
   mysql> show global variables like "log_bin";
   +---------------+-------+
   | Variable_name | Value |
   +---------------+-------+
   | log_bin       | ON    |
   +---------------+-------+
   </pre>
4. Run the below command to create the sample database named `testdb`.
   <pre>
   mysql> create database testdb;
   </pre>
5. Run this to AWS DMS has bin log access that is required for replication.
   <pre>
   mysql> create database testdb;
   </pre>
6. Exit from the SQL prompt and open the command-line terminal.
7. At the command-line prompt run the below command to create the sample table named in `testdb` database.
8. Generate test data.
   <pre>
   (.venv) $ python tests/gen_fake_mysql_data.py \
                    --database <i>your-database-name</i> \
                    --table <i>your-table-name</i> \
                    --user <i>user-name</i> \
                    --password <i>password</i> \
                    --host <i>db-cluster-name</i>.cluster-<i>xxxxxxxxxxxx</i>.<i>region-name</i>.rds.amazonaws.com \
                    --max-count 200
   </pre>
9.  Check s3 and you will see data in the s3 location such as:
     <pre>
     s3://<i>target-s3-bucket</i>/<i>target-s3-prefix</i>/<i>your-database-name</i>/<i>your-table-name</i>/
     </pre>

#### Clean Up
1. Stop the DMS Replication task by replacing the ARN in below command.
   <pre>
   (.venv) $ aws dms stop-replication-task --replication-task-arn <i>dms-task-arn</i> --region <i>region-name</i>
   </pre>
2. Delete the CloudFormation stack by running the below command.
   <pre>
   (.venv) $ cdk destroy
   </pre>


## References

 * [aws-dms-deployment-using-aws-cdk](https://github.com/aws-samples/aws-dms-deployment-using-aws-cdk) - AWS DMS deployment using AWS CDK (Python)
 * [aws-dms-msk-demo](https://github.com/aws-samples/aws-dms-msk-demo) - Streaming Data to Amazon MSK via AWS DMS