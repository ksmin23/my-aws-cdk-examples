
# PostgreSQL

![postgresql-arch](./postgresql-arch.svg)

This is a sample project for CDK development with Python.

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

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
(.venv) $ cdk synth -c db_cluster_name='<i>db-cluster-name</i>' --all
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy -c db_cluster_name='<i>db-cluster-name</i>' --all
</pre>

## Clean Up

Delete the CloudFormation stacks by running the below command.

```
(.venv) $ cdk destroy --all
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

# Example

1. (1) Install PostgreSQL 13 on Amazon Linux 2

   <pre>
   $ sudo amazon-linux-extras install epel
   $ sudo amazon-linux-extras | grep postgres
   $ sudo amazon-linux-extras enable postgresql13
   $ sudo yum clean metadata
   $ sudo yum install -y postgresql
   </pre>

   (2) Install PostgreSQL Client on Ubuntu
   <pre>
   $ sudo apt install -y postgresql-client
   </pre>

2. Connect to PostgreSQL

    :information_source: The `username` and `password` of the master user are stored in the [AWS Secrets Manager](https://console.aws.amazon.com/secretsmanager/listsecrets) as a name such as `rds!cluster-xxxxxxxxxxxx`. (For more information, see [here](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-secrets-manager.html).)

    <pre>
    $ psql -h <i>db-cluster-name</i>.cluster-<i>xxxxxxxxxxxx</i>.<i>region-name</i>.rds.amazonaws.com -Upostgres -W
    psql (13.3, server 13.4)
    SSL connection (protocol: TLSv1.2, cipher: ECDHE-RSA-AES256-GCM-SHA384, bits: 256, compression: off)
    Type "help" for help.

    postgres=>
    postgres=> \l
                                  List of databases
    Name    |  Owner   | Encoding |   Collate   |    Ctype    |   Access privileges
    -----------+----------+----------+-------------+-------------+-----------------------
    postgres  | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
    rdsadmin  | rdsadmin | UTF8     | en_US.UTF-8 | en_US.UTF-8 | rdsadmin=CTc/rdsadmin
    template0 | rdsadmin | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/rdsadmin          +
              |          |          |             |             | rdsadmin=CTc/rdsadmin
    template1 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
              |          |          |             |             | postgres=CTc/postgres
    (4 rows)

    postgres=> SELECT version();
                                                version
    -------------------------------------------------------------------------------------------------
    PostgreSQL 13.4 on x86_64-pc-linux-gnu, compiled by x86_64-pc-linux-gnu-gcc (GCC) 7.4.0, 64-bit
    (1 row)

    postgres=>
    </pre>

# PostgreSQL cheat sheet for MySQL users

### General hints on PostgreSQL
- `\?` opens the command overview
- `\d` lists things: `\du` lists users, `\dt` lists tables etc

### Command comparison

| MySQL command | PostgreSQL equivalent |
|---------------|-----------------------|
| mysql -u $USERNAME -p | psql -u postgres |
| SHOW DATABASES | \l[ist1] |
| USE some_database | \c some_database |
| SHOW TABLES | \dt |
| DESCRIBE some_table | \d+ some_table |
| SHOW INDEX FROM some_table | \di |
| CREATE USER username IDENTIFIED BY 'password' | CREATE ROLE username WITH createdb LOGIN [PASSWORD 'password']; |
| GRANT ALL PRIVILEGES ON database.\* TO username@localhost | GRANT ALL PRIVILEGES ON DATABASE database TO username; |
| SELECT * FROM table LIMIT 10\G; | \x on |

## References

 * [Supported DB engines for DB instance classes](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html#Concepts.DBInstanceClass.Support)
 * [PostgreSQL Cheat Sheet](https://postgrescheatsheet.com/#/connections)
 * [Postgresql Manuals](https://www.postgresql.org/docs/)
 * [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)
 * [Password management with Amazon RDS and AWS Secrets Manager](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-secrets-manager.html)
