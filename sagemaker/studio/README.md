
# Amazon SageMaker Studio

![studio-vpc-internet](./studio-vpc-internet.png)

This CDK Python project is for Amazon SageMaker Studio.

By default, SageMaker Studio provides a network interface that allows communication with the internet through a VPC managed by SageMaker.
Traffic to AWS services like Amazon S3 and CloudWatch goes through an internet gateway, as does traffic that accesses the SageMaker API and SageMaker runtime. Traffic between the domain and your Amazon EFS volume goes through the VPC that you specified when you onboarded to Studio or called the [CreateDomain](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_CreateDomain.html) API.
The above diagram shows the default configuration.

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
(.venv) $ cdk synth --all
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy --all
</pre>

If you want to set `JupyterLab3` to the default JupyterLab, you can do like this:

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
(.venv) $ cdk synth -c sagmaker_jupyterlab_arn='(optional) <i>default-JupterLab-image-arn</i>' --all
</pre>

Use `cdk deploy` command to create the stack shown above with `JupyterLab3` as the default JupyerLab.

<pre>
(.venv) $ cdk deploy -c sagmaker_jupyterlab_arn='(optional) <i>default-JupterLab-image-arn</i>' --all
</pre>

For example, if we try to set `JupyterLab3` to the default JupyterLab in `us-east-1` region, we can deploy like this:
<pre>
(.venv) $ cdk deploy -c sagmaker_jupyterlab_arn='arn:aws:sagemaker:<i>us-east-1:081325390199:image/jupyter-server-3</i>' --all
</pre>

Otherwise, you can pass context varialbes by `cdk.contex.json` file. Here is an example:
<pre>
(.venv) $ cat cdk.context.json
{
  "vpc_name": "default",
  "sagmaker_jupyterlab_arn": "arn:aws:sagemaker:us-east-1:081325390199:image/jupyter-server-3"
}
</pre>

For more information about the available JupyterLab versions for each Region, see [Amazon SageMaker - Setting a default JupyterLab version](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-jl.html#studio-jl-set)

> :information_source: `-c sagmaker_jupyterlab_arn` option is not required when synthizing or deploying CDK stacks if you do not want to set `JupyterLab3` to the default JupyterLab.

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

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

## Learn more

 * [Securing Amazon SageMaker Studio connectivity using a private VPC (2020-10-22)](https://aws.amazon.com/blogs/machine-learning/securing-amazon-sagemaker-studio-connectivity-using-a-private-vpc/)
 * [Connect SageMaker Studio Notebooks in a VPC to External Resources](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-notebooks-and-internet-access.html)
 * [Amazon SageMaker - Setting a default JupyterLab version](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-jl.html#studio-jl-set)
 * [SageMaker Studio Permissions Required to Use Projects](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-projects-studio-updates.html)
 * [Automate Amazon SageMaker Studio setup using AWS CDK (2021-06-16)](https://aws.amazon.com/ko/blogs/machine-learning/automate-amazon-sagemaker-studio-setup-using-aws-cdk/)
   * [aws-samples/aws-cdk-sagemaker-studio](https://github.com/aws-samples/aws-cdk-sagemaker-studio)
 * [Set up Amazon SageMaker Studio with Jupyter Lab 3 using the AWS CDK (2023-01-23)](https://aws.amazon.com/ko/blogs/machine-learning/set-up-amazon-sagemaker-studio-with-jupyter-lab-3-using-the-aws-cdk/)
   * [aws-cdk-native-sagemaker-studio](https://github.com/aws-samples/aws-cdk-native-sagemaker-studio/tree/e72e64b8631510f5f4d4f92306d145a2eaed1092)

Enjoy!
