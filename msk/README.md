
# Managed Service for Kafka (MSK) CDK Python project!

![msk-arch](./msk-arch.svg)

This is a sample project for Python development with CDK.

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
$ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
$ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
$ cdk -c vpc_name='<your-existing-vpc-name>' -c kafka_cluster_name='<kafka-cluster-name>' synth
```

Use `cdk deploy` command to create the stack shown above,

```
$ cdk -c vpc_name='<your-existing-vpc-name>' -c kafka_cluster_name='<kafka-cluster-name>' deploy
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

After MSK is succesfully created, you can now create topic, and produce and consume data on the topic in MSK as the following example.

First, you should generate ssh key to access MSK client EC2 Host.
```
$ ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (~/.ssh/id_rsa): path/my-rsa-key
```

Next, you send the ssh public key into your EC2 Host.

```
$ aws ec2-instance-connect send-ssh-public-key \
--instance-id i-1234567890abcdef0 \
--instance-os-user ec2-user \
--availability-zone us-east-1a \
--ssh-public-key file://path/my-rsa-key.pub
$ ssh -i /path/my-rsa-key ec2-user@10.0.0.0
```

After connect your EC2 Host, you can create a topic on the client host.

```
$ cd opt/kafka
$ export ZooKeeperConnectionString=Your-ZooKeeper-Servers
$ bin/kafka-topics.sh --create \
--zookeeper $ZooKeeperConnectionString \
--replication-factor 3 \
--partitions 1 \
--topic AWSKafkaTutorialTopic
```

To produce data on the topic, run the following command.

```
$ export BootstrapBrokerString=Your-Broker-Servers
$ bin/kafka-console-producer.sh \
--broker-list $BootstrapBrokerString \
--topic AWSKafkaTutorialTopic
```

To consume data on the topic, open another terminal and connect the client host, and then run `kafka-console-consumer.sh` command.

```
$ aws ec2-instance-connect send-ssh-public-key \
--instance-id i-1234567890abcdef0 \
--instance-os-user ec2-user \
--availability-zone us-east-1a \
--ssh-public-key file://path/my-rsa-key.pub
$ ssh -i /path/my-rsa-key ec2-user@10.0.0.0
$ bin/kafka-console-consumer.sh \
--bootstrap-server $BootstrapBrokerString \
--topic AWSKafkaTutorialTopic \
--from-beginning
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
