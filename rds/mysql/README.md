
# MySQL

![mysql-arch](./mysql-arch.svg)

This is a CDK Python project to deploy MySQL on AWS.

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
(.venv) $ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
(.venv) % .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
(.venv) $ pip install -r requirements.txt
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy --all
</pre>

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

Enjoy!

# Example
### Connect to MySQL
1. Connecting to MySQL

    :information_source: The MySQL `username` and `password` are stored in the [AWS Secrets Manager](https://console.aws.amazon.com/secretsmanager/listsecrets) as a name such as `DatabaseSecret-xxxxxxxxxxxx`.

    <pre>
    $ mysql -h <i>db-instance-name</i>.<i>xxxxxxxxxxxx</i>.<i>region-name</i>.rds.amazonaws.com -uadmin -p
    Welcome to the MariaDB monitor.  Commands end with ; or \g.
    Your MySQL connection id is 20
    Server version: 8.0.23 Source distribution

    Copyright (c) 2000, 2018, Oracle, MariaDB Corporation Ab and others.

    Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

    MySQL [(none)]>
    </pre>

2. Creating MySQL User

    ```
    MySQL [(none)]> SHOW DATABASES;
    +--------------------+
    | Database           |
    +--------------------+
    | information_schema |
    | mysql              |
    | performance_schema |
    | sys                |
    +--------------------+
    4 rows in set (0.00 sec)

    MySQL [(none)]> SELECT user FROM mysql.user;
    +---------------+
    | user          |
    +---------------+
    | admin         |
    | rdsproxyadmin |
    | mysql.sys     |
    | rdsadmin      |
    +---------------+
    3 rows in set (0.00 sec)

    MySQL [(none)]> CREATE USER 'guest'@'%' IDENTIFIED BY 'password';
    MySQL [(none)]> GRANT SELECT, PROCESS, SHOW DATABASES, CREATE VIEW, SHOW VIEW, SELECT INTO S3 ON *.* TO 'guest'@'%';
    MySQL [(none)]> FLUSH PRIVILEGES;
    MySQL [(none)]> SHOW GRANTS FOR 'guest'@'%';
    +-----------------------------------------------------------------------------------------------------+
    | Grants for guest@%                                                                                  |
    +-----------------------------------------------------------------------------------------------------+
    | GRANT SELECT, PROCESS, SHOW DATABASES, CREATE VIEW, SHOW VIEW, SELECT INTO S3 ON *.* TO 'guest'@'%' |
    +-----------------------------------------------------------------------------------------------------+
    1 row in set (0.00 sec)
    MySQL [(none)]> SELECT user FROM mysql.user;
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

    MySQL [(none)]>
    ```

3. Connecting to the database as a new MySQL user

    <pre>
    $ mysql -h <i>db-instance-name</i>.<i>xxxxxxxxxxxx</i>.<i>region-name</i>.rds.amazonaws.com -uguest -p
    Welcome to the MariaDB monitor.  Commands end with ; or \g.
    Your MySQL connection id is 20
    Server version: 8.0.23 Source distribution

    Copyright (c) 2000, 2018, Oracle, MariaDB Corporation Ab and others.

    Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

    MySQL [(none)]> SHOW DATABASES;
    +--------------------+
    | Database           |
    +--------------------+
    | information_schema |
    | mysql              |
    | performance_schema |
    | sys                |
    +--------------------+
    4 rows in set (0.00 sec)

    MySQL [(none)]>
    </pre>

4. Connecting to MySQL Readonly endpoint

    <pre>
    $ mysql -h <i>db-instance-name</i>.<i>xxxxxxxxxxxx</i>.<i>region-name</i>.rds.amazonaws.com -uadmin -p
    Welcome to the MariaDB monitor.  Commands end with ; or \g.
    Your MySQL connection id is 20
    Server version: 8.0.23 Source distribution

    Copyright (c) 2000, 2018, Oracle, MariaDB Corporation Ab and others.

    Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

    MySQL [(none)]> SHOW DATABASES;
    +--------------------+
    | Database           |
    +--------------------+
    | information_schema |
    | mysql              |
    | performance_schema |
    | sys                |
    +--------------------+
    4 rows in set (0.01 sec)

    MySQL [(none)]> CREATE DATABASE test;
    ERROR 1290 (HY000): The MySQL server is running with the --read-only option so it cannot execute this statement
    MySQL [(none)]>
    </pre>

# References

 * [Amazon RDS for MySQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_MySQL.html)
