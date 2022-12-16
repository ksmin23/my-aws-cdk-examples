
# MSK Serverless CDK Python project!

![msk-serverless-arch](./msk-serverless-arch.svg)

This is a blank project for CDK development with Python.

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
(.venv) $ cdk synth -c vpc_name=<i>your-vpc-name</i> \
            -c msk_cluster_name=<i>your-msk-cluster-name</i> \
            --all
</pre>

Use `cdk deploy` command to create the stack shown above,

<pre>
(.venv) $ cdk deploy -c vpc_name=<i>your-vpc-name</i> \
            -c msk_cluster_name=<i>your-msk-cluster-name</i> \
            --all
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Run Tests

<pre>
$ export MSK_SERVERLESS_CLUSTER_ARN=$(aws kafka list-clusters-v2 | jq -r '.ClusterInfoList[] | select(.ClusterName == "msk-serverless-tutorial-cluster") | .ClusterArn')
$ aws kafka describe-cluster-v2 --cluster-arn $MSK_SERVERLESS_CLUSTER_ARN
{
    "ClusterInfo": {
        "ClusterType": "SERVERLESS",
        "ClusterArn": "arn:aws:kafka:us-east-1:123456789012:cluster/msk-serverless-tutorial-cluster/813876e5-2023-4882-88c4-58ad8599da5a-s2",
        "ClusterName": "msk-serverless-tutorial-cluster",
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
                        "sg-5fa12d01"
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

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

 * [Getting started using MSK Serverless clusters](https://docs.aws.amazon.com/msk/latest/developerguide/serverless-getting-started.html)
 * [Analyze real-time streaming data in Amazon MSK with Amazon Athena (2022-12-15)](https://aws.amazon.com/ko/blogs/big-data/analyze-real-time-streaming-data-in-amazon-msk-with-amazon-athena/)
