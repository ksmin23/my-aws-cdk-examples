
# Amazon MemoryDB for Valkey

![amazon-memorydb-for-valkey](./amazon-memorydb-for-valkey.svg)

This is a CDK Python project for Amazon MemoryDB for Valkey cluster.

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
  "memorydb": {
    "node_type": "db.r7g.xlarge",
    "cluster_name": "valkeydb",
    "engine": "Valkey",
    "engine_version": "7.3",
    "num_shards": 3,
    "num_replicas_per_shard": 1
  }
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

## Verify

After a few minutes, the cluster is running and you can connect using the [Valkey command line interface](https://valkey.io/topics/cli/).

All MemoryDB clusters run in a virtual private cloud (VPC).
You need to EC2 instance or Cloud9 in your VPC to access MemoryDB clusters.
Also either EC2 instance or Cloud9 must be given a proper security group such as `memorydb-client-sg` created in the stack above.

### Connect to Amazon MemoryDB using Valkey command line interface

<pre>
$ wget https://github.com/valkey-io/valkey/archive/refs/tags/7.2.7.tar.gz
$ tar -xzvf 7.2.7.tar.gz
$ cd valkey-7.2.7
$ make BUILD_TLS=yes
$ sudo make install
$ MEMORYDB_CLUSTER_ENDPOINT=$(aws cloudformation describe-stacks --stack-name <i>MemoryDBStack</i> \
| jq -r '.Stacks[0].Outputs | map(select(.OutputKey == "MemoryDBClusterEndpoint")) | .[0].OutputValue')
$ valkey-cli -h <i>${MEMORYDB_CLUSTER_ENDPOINT}</i> -p 6379 -c --tls
clustercfg.<i>your-memorydb-name</i>.memorydb.<i>region</i>.amazonaws.com:6379>
</pre>

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

## Learn more

 * [(AWS Blog) Get started with Amazon MemoryDB for Valkey (2024-10-08)](https://aws.amazon.com/blogs/database/get-started-with-amazon-memorydb-for-valkey/)
 * [(AWS Blog) Amazon ElastiCache and Amazon MemoryDB announce support for Valkey (2024-10-08)](https://aws.amazon.com/blogs/database/amazon-elasticache-and-amazon-memorydb-announce-support-for-valkey/)
 * [Amazon MemoryDB Engine versions](https://docs.aws.amazon.com/memorydb/latest/devguide/engine-versions.html)
 * [Amazon MemoryDB Restricted commands](https://docs.aws.amazon.com/memorydb/latest/devguide/restrictedcommands.html)
 * [Valkey Documentation](https://valkey.io/docs/)
 * [(GitHub) Valkey](https://github.com/valkey-io)

Enjoy!
