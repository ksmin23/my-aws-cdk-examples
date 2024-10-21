
# Amazon Keyspaces (for Apache Cansandra) CDK Python project!

![amazon_keyspaces-arch.svg](./amazon_keyspaces-arch.svg)

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

### Deploy

Before synthesizing the CloudFormation, you should set approperly the cdk context configuration file, `cdk.context.json`.

For example:

```
{
  "keyspace_config": {
    "keyspace_name": "amazon",
    "replication_specification": {
      "replication_strategy": "SingleRegionStrategy"
    }
  },
  "keyspace_tables": [
    {
      "keyspace_name": "amazon",
      "partition_key_columns": [
        {
          "column_name": "id",
          "column_type": "text"
        }
      ],
      "clustering_key_columns": [
        {
          "column": {
            "column_name": "time",
            "column_type": "timeuuid"
          },
          "order_by": "ASC"
        }
      ],
      "regular_columns": [
        {
          "column_name": "event",
          "column_type": "text"
        }
      ],
      "table_name": "eventstore",
      "billing_mode": {
        "mode": "ON_DEMAND"
      },
      "point_in_time_recovery_enabled": true,
      "tags": {
        "domain": "shoppingcart",
        "app": "acme-commerce",
        "pii": "true"
      }
    }
  ]
}
```

This `cdk.context.json` is used to create a keyspace named `amazon` and a table named `eventstore`.
`amazon.eventstore` can be created with the following command with a csqlsh session.

```
CREATE TABLE amazon.eventstore(
  id text,
  time timeuuid,
  event text,
  PRIMARY KEY(id, time))
WITH CUSTOM_PROPERTIES = {
  'capacity_mode':{'throughput_mode':'PAY_PER_REQUEST'},
  'point_in_time_recovery':{'status':'enabled'}
} AND TAGS = {'domain': 'shoppingcart',
              'app': 'acme-commerce',
              'pii': 'true'};
```

At this point you can now synthesize the CloudFormation template for this code.

```
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=us-east-1 # your-aws-account-region
(.venv) $ cdk synth --all
```

Now we will be able to deploy all the CDK stacks at once like this:

```
(.venv) $ cdk deploy --require-approval never --all
```

## Clean Up

Delete the CloudFormation stacks by running the below command.

```
(.venv) $ cdk destroy --all
```

## Example

1. Connect to EC2 instance to accss Amazon Keyspace (e.g., `i-001234a4bf70dec41EXAMPLE` is an EC2 Instance ID of the bastion host)

    ```
    % mssh ec2-user@i-001234a4bf70dec41EXAMPLE
    ```

2. To confirm that `cqlsh-expansion` package is installed, you can run `cqlsh-expansion` --version.

    ```
    [ec2-user@ip-172-31-4-195 ~]$ cqlsh-expansion --version
    cqlsh 6.1.0
    ```

3. To configure the `cqlsh-expansion`, run the following command.

    ```
    [ec2-user@ip-172-31-4-195 ~]$ cqlsh-expansion.init
    Initializing .cassandra directory with SSL cert and cqlshrc file in user directory
    Creating .cassandra directory in home path /home/ec2-user
    Copying cert from /usr/local/lib/python3.7/site-packages/cqlsh_expansion/sf-class2-root.crt to /home/ec2-user/.cassandra/sf-class2-root.crt
    Copying cqlshrc from /usr/local/lib/python3.7/site-packages/cqlsh_expansion/cqlshrc_template to /home/ec2-user/.cassandra/cqlshrc
    Post installation configuration for expansion utility completed
    ```

4. Connecting to Amazon Keyspaces using the **cqlsh-expansion**

    ```
    [ec2-user@ip-172-31-4-195 ~]$ export AWS_DEFAULT_REGION=us-east-1
    [ec2-user@ip-172-31-4-195 ~]$ cqlsh-expansion cassandra.us-east-1.amazonaws.com 9142 --ssl
    Connected to Amazon Keyspaces at cassandra.us-east-1.amazonaws.com:9142
    [cqlsh 6.1.0 | Cassandra 3.11.2 | CQL spec 3.4.4 | Native protocol v4]
    Use HELP for help.
    cqlsh current consistency level is ONE.
    cqlsh>
    ```

  * Check for table creation status

    ```
    cqlsh> DESCRIBE Keyspaces

    system_schema  system_schema_mcs  system  system_multiregion_info  amazon

    cqlsh> DESCRIBE TABLES
    ...

    Keyspace amazon
    ---------------
    eventstore

    cqlsh> DESCRIBE TABLE amazon.eventstore;

    CREATE TABLE amazon.eventstore (
        id text,
        time timeuuid,
        event text,
        PRIMARY KEY (id, time)
    ) WITH CLUSTERING ORDER BY (time ASC)
        AND bloom_filter_fp_chance = 0.01
        AND caching = {'class': 'com.amazonaws.cassandra.DefaultCaching'}
        AND comment = ''
        AND compaction = {'class': 'com.amazonaws.cassandra.DefaultCompaction'}
        AND compression = {'class': 'com.amazonaws.cassandra.DefaultCompression'}
        AND crc_check_chance = 1.0
        AND dclocal_read_repair_chance = 0.0
        AND default_time_to_live = 0
        AND gc_grace_seconds = 7776000
        AND max_index_interval = 2048
        AND memtable_flush_period_in_ms = 3600000
        AND min_index_interval = 128
        AND read_repair_chance = 0.0
        AND speculative_retry = '99PERCENTILE';

    cqlsh> SELECT keyspace_name, table_name, status
      ... FROM system_schema_mcs.tables
      ... WHERE keyspace_name = 'amazon' AND table_name = 'eventstore';

    keyspace_name | table_name | status
    ---------------+------------+--------
            amazon | eventstore | ACTIVE

    (1 rows)
    cqlsh>
    ```

  * Insert sample data

    ```
    cqlsh> CONSISTENCY LOCAL_QUORUM;
    Consistency level set to LOCAL_QUORUM.
    cqlsh> INSERT INTO amazon.eventstore(id, time, event)
      ...                   VALUES ('1', now(), '{eventtype:\"click-cart\"}');
    cqlsh> INSERT INTO amazon.eventstore(id, time, event)
      ...                   VALUES ('2', now(), '{eventtype:\"showcart\"}');
    cqlsh> INSERT INTO amazon.eventstore(id, time, event)
      ...                   VALUES ('3', now(), '{eventtype:\"clickitem\"}') IF NOT EXISTS;

    [applied]
    -----------
          True

    cqlsh> SELECT * FROM amazon.eventstore;

    id | time                                 | event
    ----+--------------------------------------+----------------------------
      2 | 66493011-61c8-11ee-816b-2128d058fb17 |   {eventtype:\"showcart\"}
      1 | 60c300d1-61c8-11ee-816b-2128d058fb17 | {eventtype:\"click-cart\"}
      3 | 6d7965d1-61c8-11ee-816b-2128d058fb17 |  {eventtype:\"clickitem\"}

    (3 rows)
    cqlsh>
    ```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

 * [Using **cqlsh** to connect to Amazon Keyspaces](https://docs.aws.amazon.com/keyspaces/latest/devguide/programmatic.cqlsh.html)
 * [cqlsh-expansion](https://pypi.org/project/cqlsh-expansion/) - The utility extends native `cqlsh` functionality to include cloud native capabilities
 * [Loading data into Amazon Keyspaces with cqlsh (2020-04-21)](https://aws.amazon.com/blogs/database/loading-data-into-amazon-mcs-with-cqlsh/)
 * [How to set up command-line access to Amazon Keyspaces (for Apache Cassandra) by using the new developer toolkit Docker image (2021-01-06)](https://aws.amazon.com/blogs/database/how-to-set-up-command-line-access-to-amazon-keyspaces-for-apache-cassandra-by-using-the-new-developer-toolkit-docker-image/)
 * [CQL language reference for Amazon Keyspaces (for Apache Cassandra)](https://docs.aws.amazon.com/keyspaces/latest/devguide/cql.html)
 * [CQL for Apache Cassandra™ 2.2 and 3.x](https://docs.datastax.com/en/cql-oss/3.x/cql/cql_reference/cqlReferenceTOC.html)
 * [Connect using the EC2 Instance Connect CLI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-methods.html#ec2-instance-connect-connecting-ec2-cli)
   <pre>
   $ sudo pip install ec2instanceconnectcli
   $ mssh ec2-user@<i>i-001234a4bf70dec41EXAMPLE</i> # ec2-instance-id
   </pre>
