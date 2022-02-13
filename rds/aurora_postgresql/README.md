
# Aurora PostgreSQL

This is a sample project for Python development with CDK.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the .env
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
$ source .env/bin/activate
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
              -c vpc_name='<i>your-existing-vpc-name</i>' \
              -c db_secret_name='<i>db-secret-name</i>' \
              -c db_cluster_name='<i>db-cluster-name</i>'
</pre>

:information_source: Before you deploy this project, you should create an AWS Secret for your RDS Admin user. You can create an AWS Secret like this:

<pre>
$ aws secretsmanager create-secret \
    --name <i>"your_db_secret_name"</i> \
    --description "<i>(Optional) description of the secret</i>" \
    --secret-string '{"username": "postgres", "password": <i>"password_of_at_last_8_characters"</i>}'
</pre>

For example,

<pre>
$ aws secretsmanager create-secret \
    --name "dev/rds/admin" \
    --description "admin user for rds" \
    --secret-string '{"username": "postgres", "password": <i>"your admin password"</i>}'
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy \
              -c vpc_name='<i>your-existing-vpc-name</i>' \
              -c db_secret_name='<i>db-secret-name</i>' \
              -c db_cluster_name='<i>db-cluster-name</i>'
</pre>

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

# Example

1. Install PostgreSQL 13 on Amazon Linux 2

   <pre>
   $ sudo amazon-linux-extras install epel
   $ sudo amazon-linux-extras | grep postgres
   $ sudo amazon-linux-extras enable postgresql13
   $ sudo yum clean metadata
   $ $ sudo yum install -y postgresql
   </pre>

2. Connect to Aurora PostgreSQL

    <pre>
    $ psql -h <i>db-cluster-name</i>.cluster-<i>xxxxxxxxxxxx</i>.<i>region-name</i>.rds.amazonaws.com -Upostgres -W
    psql (13.3, server 13.4)
    SSL connection (protocol: TLSv1.2, cipher: ECDHE-RSA-AES256-GCM-SHA384, bits: 256, compression: off)
    Type "help" for help.

    postgres=>
    </pre>

# References

 * [PostgreSQL Cheat Sheet](https://postgrescheatsheet.com/#/connections)
 * [Postgresql Manuals](https://www.postgresql.org/docs/)
 * [Best practices with Amazon Aurora PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.BestPractices.html)
