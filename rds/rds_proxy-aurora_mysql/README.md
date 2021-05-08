
# RDS Proxy + Aurora MySQL

![rds_proxy-aurora_mysql-arch](./rds_proxy-aurora_mysql-arch.svg)

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
$ python3 -m venv .env
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .env/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .env\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

<pre>
$ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
$ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
$ cdk -c vpc_name='<i>your-existing-vpc-name</i>' \
  -c db_cluster_name='<i>db-cluster-name</i>>' \
  -c db_secret_name='<i>db-secret-name</i>' \
  synth
</pre>

:information_source: Before you deploy this project, you should create an AWS Secret for your RDS Admin user. You can create an AWS Secret like this:

<pre>
$ aws secretsmanager create-secret \
    --name <i>"your_db_secret_name"</i> \
    --description "<i>(Optional) description of the secret</i>" \
    --secret-string '{"username": "admin", "password": <i>"password_of_at_last_8_characters"</i>}'
</pre>

For example,

<pre>
$ aws secretsmanager create-secret \
    --name "dev/rds/admin" \
    --description "admin user for rds" \
    --secret-string '{"username": "admin", "password": <i>"your admin password"</i>}'
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
$ cdk -c vpc_name='<i>your-existing-vpc-name</i>' \
  -c db_cluster_name='<i>db-cluster-name</i>' \
  -c db_secret_name='<i>db-secret-name</i>' \
  deploy
</pre>

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

# Example

1. Connecting to Aurora MySQL using RDS Proxy

```
$ mysql -h the-proxy.proxy-demo.us-east-1.rds.amazonaws.com -uadmin -p
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 947748268
Server version: 5.7.12-log MySQL Community Server (GPL)

Copyright (c) 2000, 2020, Oracle and/or its affiliates. All rights reserved.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql>
```

2. Creating MySQL User
   
```
mysql> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
4 rows in set (0.00 sec)

mysql> SELECT user FROM mysql.user;
+---------------+
| user          |
+---------------+
| admin         |
| rdsproxyadmin |
| mysql.sys     |
| rdsadmin      |
+---------------+
3 rows in set (0.00 sec)

mysql> CREATE USER 'guest'@'%' IDENTIFIED BY 'password';
mysql> GRANT SELECT, PROCESS, SHOW DATABASES, CREATE VIEW, SHOW VIEW, SELECT INTO S3 ON *.* TO 'guest'@'%';
mysql> FLUSH PRIVILEGES;
mysql> SHOW GRANTS FOR 'guest'@'%';
+-----------------------------------------------------------------------------------------------------+
| Grants for guest@%                                                                                  |
+-----------------------------------------------------------------------------------------------------+
| GRANT SELECT, PROCESS, SHOW DATABASES, CREATE VIEW, SHOW VIEW, SELECT INTO S3 ON *.* TO 'guest'@'%' |
+-----------------------------------------------------------------------------------------------------+
1 row in set (0.00 sec)
mysql> SELECT user FROM mysql.user;
+---------------+
| user          |
+---------------+
| admin         |
| guest         |
| rdsproxyadmin |
| mysql.sys     |
| rdsadmin      |
+---------------+
4 rows in set (0.00 sec)

mysql>
```

3. Creating AWS Secret for a new MySQL User 

<pre>
aws secretsmanager create-secret \
    --name "<i>guest_secret_name</i>" \
    --description "application user" \
    --secret-string '{"username": "<i>guest</i>", "password": "<i>choose_your_own_password</i>"}'
</pre>

4. Modifying IAM Role so that RDS Proxy can access the secret of new MySQL User

<pre>
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": [
                "arn:aws:secretsmanager:<i>region_name</i>:<i>account_id:secret</i>:<i>secret_name_1-??????</i>",
                "arn:aws:secretsmanager:<i>region_name</i>:<i>account_id:secret</i>:<i>secret_name_2-??????</i>",
            ],
            "Effect": "Allow"
        }
    ]
}
</pre>

5. Connecting to the database as a new MySQL user
   
```
$ mysql -h the-proxy.proxy-demo.us-east-1.rds.amazonaws.com -uguest -p
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 2444658406
Server version: 5.7.12-log MySQL Community Server (GPL)

Copyright (c) 2000, 2020, Oracle and/or its affiliates. All rights reserved.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
4 rows in set (0.00 sec)

mysql>
```

## References
- [Managing connections with Amazon RDS Proxy](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html)
- [Amazon Aurora MySQL reference](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Reference.html)
