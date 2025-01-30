
# EC2 Service with Task Networking on Amazon ECS

This is a CDK Python project to deploy an EC2 Service with Task Networking on Amazon ECS.

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
> To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Prerequisites

**Set up `cdk.context.json`**

Then, we need to set approperly the cdk context configuration file, `cdk.context.json`.

For example,

```
{
  "ecr": [
    {
      "repository_name": "nginx",
      "docker_image_name": "nginx",
      "tag": "stable-perl"
    }
  ],
  "ecs_cluster_name": "awsvpc-ecs-demo",
  "private_dns_namespace_name": "awsvpc-ecs-demo.local"
}
```

**Bootstrap AWS environment for AWS CDK app**

Also, before any AWS CDK app can be deployed, you have to bootstrap your AWS environment to create certain AWS resources that the AWS CDK CLI (Command Line Interface) uses to deploy your AWS CDK app.

Run the `cdk bootstrap` command to bootstrap the AWS environment.

```
(.venv) $ cdk bootstrap
```

### Deploy

At this point you can now synthesize the CloudFormation template for this code.

```
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all
```

Use `cdk deploy` command to create the stack shown above.

```
(.venv) $ cdk deploy --require-approval never --all
```

We can list all the CDK stacks by using the `cdk list` command prior to deployment.

```
(.venv) $ cdk list
```

## How to get the container URL

After deploying all CDK stacks, we can find the nginx container url using the following command:

```
aws cloudformation describe-stacks --stack-name EC2ServiceECSServiceStack --region ${CDK_DEFAULT_REGION} | \
  jq -r '.Stacks[0].Outputs | map(select(.OutputKey == "ServiceInternalUrl")) | .[0].OutputValue'
```

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

## References

 * [(GitHub) aws-samples/aws-cdk-examples/ecs/ecs-service-with-task-networking](https://github.com/aws-samples/aws-cdk-examples/tree/main/python/ecs/ecs-service-with-task-networking)
 * [(AWS Compute Blog) Introducing Cloud Native Networking for Amazon ECS Containers (2017-11-14)](https://aws.amazon.com/blogs/compute/introducing-cloud-native-networking-for-ecs-containers/)
 * [(AWS Compute Blog) Under the Hood: Task Networking for Amazon ECS (2017-11-14)](https://aws.amazon.com/blogs/compute/under-the-hood-task-networking-for-amazon-ecs/)
 * [(DockerHub) nginx - Official Image](https://hub.docker.com/_/nginx)
