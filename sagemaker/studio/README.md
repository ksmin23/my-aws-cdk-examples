
# Amazon SageMaker Studio

This is Amazon SageMaker Studio with CDK (Python).

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
(.venv) $ cdk synth -c vpc_name='<i>your-existing-vpc-name</i>' \
              -c sagmaker_image_arn='<i>sagemaker-image-arn</i>'
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy -c vpc_name='<i>your-existing-vpc-name</i>' \
              -c sagmaker_image_arn='<i>sagemaker-image-arn</i>'
</pre>

For example, if we try to set `JupyterLab3` to the default JupyterLab in `us-east-1` region, we can deploy like this:
<pre>
(.venv) $ cdk deploy -c vpc_name=default \
              -c sagmaker_image_arn='arn:aws:sagemaker:<i>us-east-1:081325390199:image/jupyter-server-3</i>'
</pre>

For more information about the available JupyterLab versions for each Region, see [Amazon SageMaker - Setting a default JupyterLab version](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-jl.html#studio-jl-set)

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Clean Up

Delete the CloudFormation stack by running the below command.

<pre>
(.venv) $ cdk destroy --force \
                      -c sagmaker_image_arn='<i>sagemaker-image-arn</i>'
</pre>

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

## Learn more

 * [Amazon SageMaker - Setting a default JupyterLab version](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-jl.html#studio-jl-set)
 * [Perform interactive data processing using Spark in Amazon SageMaker Studio Notebooks (2021-03-17)](https://aws.amazon.com/blogs/machine-learning/amazon-sagemaker-studio-notebooks-backed-by-spark-in-amazon-emr/)
 * [Build Amazon SageMaker notebooks backed by Spark in Amazon EMR (2018-01-05)](https://aws.amazon.com/blogs/machine-learning/build-amazon-sagemaker-notebooks-backed-by-spark-in-amazon-emr/)
 * [Amazon SageMaker - Set Up a Connection to an Amazon EMR Cluster](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-emr.html)
 * [SageMaker Studio Permissions Required to Use Projects](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-projects-studio-updates.html)
 * [Automate Amazon SageMaker Studio setup using AWS CDK (2021-06-16)](https://aws.amazon.com/ko/blogs/machine-learning/automate-amazon-sagemaker-studio-setup-using-aws-cdk/)
   * [aws-samples/aws-cdk-sagemaker-studio](https://github.com/aws-samples/aws-cdk-sagemaker-studio)

Enjoy!
