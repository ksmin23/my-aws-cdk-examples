
# Data migration from Aurora MySQL to S3 with AWS DMS

This is a blank project for Python development with CDK.

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
