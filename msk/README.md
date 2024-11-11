
# Amazon Managed Service for Kafka (MSK) CDK Python project!

![msk-arch](./msk-arch.svg)

This is a MSK project for CDK development with Python.

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
> To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Set up `cdk.context.json`
Then, we need to set approperly the cdk context configuration file, `cdk.context.json`.

For example,

```
{
  "vpc_name": "default",
  "msk_configuration": {
    "kafka_cluster_name": "MSK-Demo",
    "kafka_version": "3.6.0",
    "kafka_broker_instance_type": "express.m7g.large",
    "kafka_broker_ebs_volume_size": "100"
  }
}
```

## Deploy

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all
</pre>

Use `cdk deploy` command to create the stack shown above,

<pre>
(.venv) $ cdk deploy --require-approval never --all
</pre>

## Run Test

After MSK is succesfully created, you can now create topic, and produce and consume data on the topic in MSK as the following example.

First connect your EC2 Host using `mssh` command, you can create a topic on the client host.

<pre>
(.venv) $ mssh --region <i>us-east-1</i> ec2-user@@i-001234a4bf70dec41EXAMPLE
$ cd opt/kafka
$ export BootstrapBrokerString=<i>Your-Broker-Servers</i>
$ bin/kafka-topics.sh --create \
    --zookeeper $BootstrapBrokerString \
    --replication-factor 3 \
    --partitions 1 \
    --topic AWSKafkaTutorialTopic
</pre>

To produce data on the topic, run the following command.

<pre>
$ export BootstrapBrokerString=<i>Your-Broker-Servers</i>
$ bin/kafka-console-producer.sh \
    --bootstrap-server $BootstrapBrokerString \
    --topic AWSKafkaTutorialTopic
</pre>

To consume data on the topic, open another terminal and connect the client host, and then run `kafka-console-consumer.sh` command.

<pre>
(.venv) $ mssh --region <i>us-east-1</i> ec2-user@@i-001234a4bf70dec41EXAMPLE
$ export BootstrapBrokerString=<i>Your-Broker-Servers</i>
$ cd opt/kafka
$ bin/kafka-console-consumer.sh \
    --bootstrap-server $BootstrapBrokerString \
    --topic AWSKafkaTutorialTopic \
    --from-beginning
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


## References

 * [Amazon MSK - Supported Apache Kafka versions](https://docs.aws.amazon.com/msk/latest/developerguide/supported-kafka-versions.html)
 * [Getting Started Using Amazon MSK](https://docs.aws.amazon.com/msk/latest/developerguide/getting-started.html)
 * [Amazon MSK - Port information](https://docs.aws.amazon.com/msk/latest/developerguide/port-info.html)
 * [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
 * [Introducing Express brokers for Amazon MSK to deliver high throughput and faster scaling for your Kafka clusters (2024-11-07)](https://aws.amazon.com/blogs/aws/introducing-express-brokers-for-amazon-msk-to-deliver-high-throughput-and-faster-scaling-for-your-kafka-clusters/)
 * [Connect using the EC2 Instance Connect CLI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-methods.html#ec2-instance-connect-connecting-ec2-cli)
   <pre>
   $ sudo pip install ec2instanceconnectcli
   $ mssh <i>i-001234a4bf70dec41EXAMPLE</i> # ec2-instance-id
   </pre>


## Kafka Commands CheatSheet

 * Get Zookeeper information
   <pre>
    $ aws kafka describe-cluster-v2 --cluster-arn <i>msk_cluster_arn</i> | jq -r '.ClusterInfo.Provisioned | {ZookeeperConnectString, ZookeeperConnectStringTls}'
    $ export ZK=<i>{ZookeeperConnectString}</i>
   </pre>

 * Get Bootstrap server information
   <pre>
   $ aws kafka get-bootstrap-brokers --cluster-arn <i>msk_cluster_arn</i>
   $ export BS=<i>{BootstrapBrokerString}</i>
   </pre>

 * List Kafka toipics
   <pre>
   $ kafka-topics.sh --zookeeper $ZK \
                     --list
   </pre>

 * Create a Kafka toipic
   <pre>
   $ kafka-topics.sh --zookeeper $ZK \
                     --create \
                     --topic <i>topic_name</i> \
                     --partitions 3 \
                     --replication-factor 2
   </pre>

 * Consume records from a Kafka toipic
   <pre>
   $ kafka-console-consumer.sh --bootstrap-server $BS \
                               --topic <i>topic_name</i> \
                               --from-beginning
   </pre>

 * Produce records into a Kafka toipic
   <pre>
   $ kafka-console-producer.sh --bootstrap-server $BS \
                               --topic <i>topic_name</i>
   </pre>
