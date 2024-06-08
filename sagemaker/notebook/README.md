
# Amazon SageMaker Notebook Instance

This is a CDK Python project to deploy an Amazon SageMaker Notebook Instance.

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

Let's check all CDK Stacks with `cdk list` command.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
(.venv) $ cdk list
SageMakerNotebookVPCStack
SageMakerNotebookStack
</pre>

Then, synthesize the CloudFormation template for this code.
<pre>
(.venv) $ cdk synth --all \
              --parameters SageMakerNotebookInstanceType=<i>'your-notebook-instance-type'</i>
</pre>

Use `cdk deploy` command to create the stack shown above,

<pre>
(.venv) $ cdk deploy --require-approval never -e SageMakerNotebookVPCStack
(.venv) $ cdk deploy --require-approval never \
              --parameters SageMakerNotebookInstanceType=<i>'your-notebook-instance-type'</i> \
              -e SageMakerNotebookStack
</pre>

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

## References

 * [SageMaker Notebook Instance Lifecycle Config Samples](https://github.com/aws-samples/amazon-sagemaker-notebook-instance-lifecycle-config-samples) - A collection of sample scripts to customize Amazon SageMaker Notebook Instances using Lifecycle Configurations
 * [Resolve Amazon SageMaker lifecycle configuration timeouts](https://aws.amazon.com/premiumsupport/knowledge-center/sagemaker-lifecycle-script-timeout/) - How can I be sure that manually installed libraries persist in Amazon SageMaker if my lifecycle configuration times out when I try to install the libraries?

## Troubleshooting

 * [Getting ValidationError: Parameters: do not exist in the template while deploying](https://github.com/aws/aws-cdk/issues/6119)
   ```
   The behavior I see is if you have a CDK app with multiple stacks and if one of the stack is using cfnParameters, you will need to deploy that stack individually like below:

   cdk deploy Stack3 --parameters uploadBucketName=testbucket100

   The usual cdk deploy --all wont work even if you pass parameters on the command line.
   ```
