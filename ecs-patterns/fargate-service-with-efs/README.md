
# AWS Fargate Service using EFS

This example creates a Public Facing load balanced Fargate service with an EFS Filesystem mount.

This CDK Python project is based on this blog post: [Amazon Elastic Container Service & AWS Fargate, now support Amazon Elastic File System (2020-04-08)](https://aws.amazon.com/blogs/aws/amazon-ecs-supports-efs/)

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

### Set up `cdk.context.json`

Then, we need to set approperly the cdk context configuration file, `cdk.context.json`.

For example,

```
{
  "ecr": [
    {
      "repository_name": "cloudcmd",
      "docker_image_name": "coderaiser/cloudcmd",
      "tag": "18.5.0-alpine"
    }
  ],
  "ecs_cluster_name": "fargate-service-with-efs-cluster",
  "ecs_service_name": "cloudcmd"
}
```
> :information_source: The `coderaiser/cloudcmd` docker image is a docker image of an open source application called [Cloud Commander](https://github.com/coderaiser/cloudcmd), which is a simple drag and drop file manager.

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
FargateServiceWithEfsECRStack
FargateServiceWithEfsVpcStack
FargateServiceWithEfsALBStack
FargateServiceWithEfsECSClusterStack
FargateServiceWithEfsEFSStack
FargateServiceWithEfsECSTaskStack
FargateServiceWithEfsECSServiceStack
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

 * [(AWS Blog) Amazon Elastic Container Service & AWS Fargate, now support Amazon Elastic File System (2020-04-08)](https://aws.amazon.com/blogs/aws/amazon-ecs-supports-efs/)
 * [(GitHub) aws-cdk-examples/typescript/ecs/fargate-service-with-efs](https://github.com/aws-samples/aws-cdk-examples/tree/main/typescript/ecs/fargate-service-with-efs)
