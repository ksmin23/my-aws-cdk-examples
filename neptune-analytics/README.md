
# Amazon Neptune Analytics CDK Python project!

![neptune-analytics-arch](./neptune-analytics-arch.svg)

This is an Amazon Neptune Analytics project for CDK development with Python.

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

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

At this point you can now synthesize the CloudFormation template for this code.

```
(.venv) $ cdk synth --all
```

Use `cdk deploy` command to create the stack shown above.

```
(.venv) $ cdk deploy --all
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

 * [Amazon Neptune Analytics Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/28907bd0-e855-428a-aabd-ae2173eef31b/en-US)
 * [Build Your First Graph Application with Amazon Neptune](https://catalog.workshops.aws/neptune-deep-dive/en-US)
 * [Creating a new Neptune Analytics notebook using a AWS CloudFormation template](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/create-notebook-cfn.html)
 * [Creating a new Neptune Analytics notebook using the AWS Management Console](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/create-notebook-console.html)
 * [(GitHub) amazon-neptune-samples](https://github.com/aws-samples/amazon-neptune-samples/)
 * [(GitHub) aws/graph-notebook](https://github.com/aws/graph-notebook)
