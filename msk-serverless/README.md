
# Amazon MSK Serverless CDK Python project!

![msk-serverless-arch](./msk-serverless-arch.svg)

This is a MSK Serverless project for CDK development with Python.

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

<pre>
(.venv) $ cdk synth -c msk_cluster_name=<i>your-msk-cluster-name</i> \
                    --all
</pre>

Use `cdk deploy` command to create the stack shown above,

<pre>
(.venv) $ cdk deploy -c msk_cluster_name=<i>your-msk-cluster-name</i> \
                     --all
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Run Test

After MSK is succesfully created, you can now create topic, and produce and consume data on the topic in MSK as the following example.

1. Get cluster information
   <pre>
   $ export MSK_SERVERLESS_CLUSTER_ARN=$(aws kafka list-clusters-v2 | jq -r '.ClusterInfoList[] | select(.ClusterName == "<i>your-msk-cluster-name</i>") | .ClusterArn')
   $ aws kafka describe-cluster-v2 --cluster-arn $MSK_SERVERLESS_CLUSTER_ARN
   {
     "ClusterInfo": {
       "ClusterType": "SERVERLESS",
       "ClusterArn": "arn:aws:kafka:us-east-1:123456789012:cluster/<i>your-msk-cluster-name</i>/813876e5-2023-4882-88c4-58ad8599da5a-s2",
       "ClusterName": "<i>your-msk-cluster-name</i>",
       "CreationTime": "2022-12-16T02:26:31.369000+00:00",
       "CurrentVersion": "K2EUQ1WTGCTBG2",
       "State": "ACTIVE",
       "Tags": {},
       "Serverless": {
         "VpcConfigs": [
           {
             "SubnetIds": [
               "subnet-0113628395a293b98",
               "subnet-090240f6a94a4b5aa",
               "subnet-036e818e577297ddc"
             ],
             "SecurityGroupIds": [
               "sg-0bd8f5ce976b51769",
               "sg-0869c9987c033aaf1"
             ]
           }
         ],
         "ClientAuthentication": {
           "Sasl": {
             "Iam": {
               "Enabled": true
             }
           }
         }
       }
     }
   }
   </pre>

2. Get booststrap brokers

   <pre>
   $ aws kafka get-bootstrap-brokers --cluster-arn $MSK_SERVERLESS_CLUSTER_ARN
   {
     "BootstrapBrokerStringSaslIam": "boot-deligu0c.c1.kafka-serverless.<i>{region}</i>.amazonaws.com:9098"
   }
   </pre>

3. Connect the MSK client EC2 Host.

   You can connect to an EC2 instance using the EC2 Instance Connect CLI.<br/>
   Install `ec2instanceconnectcli` python package and Use the **mssh** command with the instance ID as follows.
   <pre>
   $ sudo pip install ec2instanceconnectcli
   $ mssh ec2-user@<i>i-001234a4bf70dec41EXAMPLE</i>
   </pre>

4. Create an Apache Kafka topic
   After connect your EC2 Host, you use the client machine to create a topic on the serverless cluster.
   Run the following command to create a topic called `msk-serverless-tutorial`.
   <pre>
   [ec2-user@ip-172-31-0-180 ~]$ export PATH=$HOME/opt/kafka/bin:$PATH
   [ec2-user@ip-172-31-0-180 ~]$ export BS=<i>your-msk-broker-endpoint</i>
   [ec2-user@ip-172-31-0-180 ~]$ kafka-topics.sh --bootstrap-server $BS --command-config client.properties --create --topic <i>msk-serverless-tutorial</i> --partitions 6 --replication-factor 2
   </pre>

5. Produce and consume data

   **(1) To produce messages**

   Run the following command to start a console producer.

   <pre>
   [ec2-user@ip-172-31-0-180 ~]$ kafka-console-producer.sh --broker-list $BS --producer.config client.properties --topic <i>msk-serverless-tutorial</i>
   </pre>

   Enter any message that you want, and press Enter. Repeat this step two or three times. Every time you enter a line and press Enter, that line is sent to your cluster as a separate message.

   **(2) To consume messages**

   Keep the connection to the client machine open, and then open a second, separate connection to that machine in a new window.

   <pre>
   [ec2-user@ip-172-31-0-180 ~]$ kafka-console-consumer.sh --bootstrap-server $BS --consumer.config client.properties --topic <i>msk-serverless-tutorial</i> --from-beginning
   </pre>

   You start seeing the messages you entered earlier when you used the console producer command.
   Enter more messages in the producer window, and watch them appear in the consumer window.


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

## References

 * [Getting started using MSK Serverless clusters](https://docs.aws.amazon.com/msk/latest/developerguide/serverless-getting-started.html)
 * [Configuration for MSK Serverless clusters](https://docs.aws.amazon.com/msk/latest/developerguide/serverless-config.html)
 * [Actions, resources, and condition keys for Apache Kafka APIs for Amazon MSK clusters](https://docs.aws.amazon.com/service-authorization/latest/reference/list_apachekafkaapisforamazonmskclusters.html)
 * [Analyze real-time streaming data in Amazon MSK with Amazon Athena (2022-12-15)](https://aws.amazon.com/ko/blogs/big-data/analyze-real-time-streaming-data-in-amazon-msk-with-amazon-athena/)
 * [Connect using the EC2 Instance Connect CLI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-methods.html#ec2-instance-connect-connecting-ec2-cli)
   <pre>
   $ sudo pip install ec2instanceconnectcli
   $ mssh <i>ec2-user</i>@<i>i-001234a4bf70dec41EXAMPLE</i> # ec2-instance-id
   </pre>
 * [ec2instanceconnectcli](https://pypi.org/project/ec2instanceconnectcli/): This Python CLI package handles publishing keys through EC2 Instance Connectand using them to connect to EC2 instances.
