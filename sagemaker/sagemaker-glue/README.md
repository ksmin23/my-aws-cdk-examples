
# Amazon SageMaker - Get Started with AWS Glue Interactive Sessions

![sagmaker-glue-arch](./sagemaker-glue-arch.svg)

This is a CDK Python project for Amazon SageMaker that allows you to have interactive sessions with AWS Glue.

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

```
(.venv) $ cdk synth --all
```

Use `cdk deploy` command to create the stack shown above.

```
(.venv) $ cdk deploy --all
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Clean Up

Delete the CloudFormation stack by running the below command.

```
(.venv) $ cdk destroy --force
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!


## Launch a Glue interactive session on SageMaker Studio

After you have created the roles, policies, and SageMaker domain, you can launch your Glue interactive session in SageMaker Studio by following the instructions: [Launch your Glue interactive session on SageMaker Studio](https://docs.aws.amazon.com/sagemaker/latest/dg/getting-started-glue-sm.html#glue-sm-launch)


## References

 * [Amazon SageMaker - Get Started with AWS Glue Interactive Sessions](https://docs.aws.amazon.com/sagemaker/latest/dg/getting-started-glue-sm.html)
 * [Magics supported by AWS Glue interactive sessions for Jupyter](https://docs.aws.amazon.com/glue/latest/dg/interactive-sessions-magics.html#interactive-sessions-supported-magics)
 * [Building an AWS Glue ETL pipeline locally without an AWS account (2020-09-21)](https://aws.amazon.com/blogs/big-data/building-an-aws-glue-etl-pipeline-locally-without-an-aws-account/)
 * [Program AWS Glue ETL scripts in PySpark](https://docs.aws.amazon.com/glue/latest/dg/aws-glue-programming-python.html)