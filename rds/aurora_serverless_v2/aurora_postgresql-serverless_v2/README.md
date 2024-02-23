
# Aurora Postgresql Serverless v2 Cluster

![aurora_postgresql-serverless_v2-cluster-arch](./aurora_postgresql-serverless_v2-cluster-arch.svg)

This is a sample project for CDK development with Python.<br/>
This project shows how to create Aurora MySQL Serverless v2 cluster.

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
$ cdk synth -c db_cluster_name=pgsql --all
```

Use `cdk deploy` command to create the stack shown above.

```
$ cdk deploy -c db_cluster_name=pgsql --require-approval never --all
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

# Example

1. Install PostgreSQL

   (1) Install PostgreSQL 13 on Amazon Linux 2
   <pre>
   $ sudo amazon-linux-extras install epel
   $ sudo amazon-linux-extras | grep postgres
   $ sudo amazon-linux-extras enable postgresql13
   $ sudo yum clean metadata
   $ sudo yum install -y postgresql
   </pre>

   (2) Install PostgreSQL 15 on Amazon Linux 2
   <pre>
   $ sudo apt update
   $ sudo apt install -y postgresql postgresql-contrib
   </pre>

2. Connect to Aurora PostgreSQL

   :information_source: The Aurora PostgreSQL `username` and `password` are stored in the [AWS Secrets Manager](https://console.aws.amazon.com/secretsmanager/listsecrets) as a name such as `DatabaseSecret-xxxxxxxxxxxx`.

   <pre>

   $ psql -h <i>db-cluster-name</i>.cluster-<i>xxxxxxxxxxxx</i>.<i>region-name</i>.rds.amazonaws.com -Upostgres -W
    psql (14.10 (Ubuntu 14.10-0ubuntu0.22.04.1), server 15.5)
    WARNING: psql major version 14, server major version 15.
            Some psql features might not work.
    SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, bits: 256, compression: off)
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
    -------------------------------------------------------------------------------------------------------------
    PostgreSQL 15.5 on aarch64-unknown-linux-gnu, compiled by aarch64-unknown-linux-gnu-gcc (GCC) 9.5.0, 64-bit
    (1 row)

    postgres=>
    </pre>

3. Create VectorDB on Aurora PostgreSQL for Amazon Knowledge Base for Amazon Bedrock

   You can create a vector database on Aurora PostgreSQL using the pgvector extension by running following code

    ```
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE SCHEMA bedrock_integration;
    CREATE TABLE bedrock_integration.bedrock_kb (
      id uuid PRIMARY KEY,
      embedding vector(1536),
      chunks text,
      metadata json
    );
    CREATE INDEX ON bedrock_integration.bedrock_kb
      USING hnsw (embedding vector_cosine_ops);
    ```

    * Database name: `postgres`
    * Table name: `bedrock_integration.bedrock_kb`
    * Vector field: `embedding`
    * Text field: `chunks`
    * Bedrock-managed metadata field: `metadata`
    * Primary key: `id`

   Also, you can check to see if the pgvector extension has been created successfully by running the following code:
    ```
    SELECT typname
    FROM pg_type
    WHERE typname = 'vector';
    ```

:information_source: For more examples of PostgreSQL queries, see [rds/sagemaker-aurora_postgresql/ipython-sql-postgresql.ipynb](../../sagemaker-aurora_postgresql/ipython-sql-postgresql.ipynb)

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

 * [(GitHub Issues) aws_rds: Add support for the Data API to DatabaseCluster construct (created at 2024-01-04)](https://github.com/aws/aws-cdk/issues/28574)
    ```
    const RDS = require('aws-cdk-lib/aws-rds');

    const dbCluster = new RDS.DatabaseCluster(this, 'AuroraServerlessV2DatabaseCluster', {
      engine: RDS.DatabaseClusterEngine.auroraPostgres({
        version: RDS.AuroraPostgresEngineVersion.VER_15_3,
      }),
      serverlessV2MinCapacity: 0.5,
      serverlessV2MaxCapacity: 2,

      writer: RDS.ClusterInstance.serverlessV2('AuroraServerlessWriter'),
      readers: [
        RDS.ClusterInstance.serverlessV2('AuroraServerlessReader0', {scaleWithWriter: true}),
      ],
    });

    // Enable the data api via "layer 1" shenanigans
    dbCluster.node.defaultChild.addOverride('Properties.EnableHttpEndpoint', true);
    ```
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
 * [Build generative AI applications with Amazon Aurora and Knowledge Bases for Amazon Bedrock (2024-02-02)](https://aws.amazon.com/blogs/database/build-generative-ai-applications-with-amazon-aurora-and-knowledge-bases-for-amazon-bedrock/)
 * [PostgreSQL Cheat Sheet](https://postgrescheatsheet.com/#/connections)

