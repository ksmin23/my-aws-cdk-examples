
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

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
(.venv) $ cdk -c vpc_name=<i>'your-existing-vpc-name'</i> synth \
    --parameters KafkaClusterName=<i>'your-kafka-cluster-name'</i> \
    --parameters KafkaVersion=<i>'your-kafka-version'</i>
</pre>

Use `cdk deploy` command to create the stack shown above,

<pre>
(.venv) $ cdk -c vpc_name=<i>'your-existing-vpc-name'</i> deploy
    --parameters KafkaClusterName=<i>'your-kafka-cluster-name'</i> \
    --parameters KafkaVersion=<i>'your-kafka-version'</i>
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Run Test

After MSK is succesfully created, you can now create topic, and produce and consume data on the topic in MSK as the following example.

First connect your EC2 Host using `mssh` command, you can create a topic on the client host.

<pre>
$ mssh --region <i>us-east-1</i> ec2-user@@i-001234a4bf70dec41EXAMPLE
$ cd opt/kafka
$ export ZooKeeperConnectionString=<i>Your-ZooKeeper-Servers</i>
$ bin/kafka-topics.sh --create \
    --zookeeper $ZooKeeperConnectionString \
    --replication-factor 3 \
    --partitions 1 \
    --topic AWSKafkaTutorialTopic
</pre>

To produce data on the topic, run the following command.

<pre>
$ export BootstrapBrokerString=<i>Your-Broker-Servers</i>
$ bin/kafka-console-producer.sh \
    --broker-list $BootstrapBrokerString \
    --topic AWSKafkaTutorialTopic
</pre>

To consume data on the topic, open another terminal and connect the client host, and then run `kafka-console-consumer.sh` command.

<pre>
$ mssh --region <i>us-east-1</i> ec2-user@@i-001234a4bf70dec41EXAMPLE
$ bin/kafka-console-consumer.sh \
    --bootstrap-server $BootstrapBrokerString \
    --topic AWSKafkaTutorialTopic \
    --from-beginning
</pre>

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation


## References

 * [Amazon MSK - Supported Apache Kafka versions](https://docs.aws.amazon.com/msk/latest/developerguide/supported-kafka-versions.html)
 * [Getting Started Using Amazon MSK](https://docs.aws.amazon.com/msk/latest/developerguide/getting-started.html)
 * [Amazon MSK - Port information](https://docs.aws.amazon.com/msk/latest/developerguide/port-info.html)
 * [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
 * [Connect using the EC2 Instance Connect CLI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-methods.html#ec2-instance-connect-connecting-ec2-cli)
   <pre>
   $ sudo pip install ec2instanceconnectcli
   $ mssh <i>i-001234a4bf70dec41EXAMPLE</i> # ec2-instance-id
   </pre>

Enjoy!
