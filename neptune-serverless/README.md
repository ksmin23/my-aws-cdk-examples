# Amazon Neptune Serverless with Jupyter Notebooks

![neptune-serverless-arch](./neptune-serverless-arch.svg)

This is an Amazon Neptune Serverless project for Python development with CDK.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the .env
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .env
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .env/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .env\Scripts\activate.bat
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
them to your `requirements.txt` file and rerun the `pip install -r requirements.txt`
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

 * [(AWS Blog) Use cases and best practices to optimize cost and performance with Amazon Neptune Serverless (2023-006-28)](https://aws.amazon.com/blogs/database/use-cases-and-best-practices-to-optimize-cost-and-performance-with-amazon-neptune-serverless/)
 * [Amazon Neptune Serverless constraints](https://docs.aws.amazon.com/neptune/latest/userguide/neptune-serverless.html#neptune-serverless-limitations)
 * [Build Your First Graph Application with Amazon Neptune](https://catalog.workshops.aws/neptune-deep-dive/en-US)
 * [Amazon Neptune Analytics Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/28907bd0-e855-428a-aabd-ae2173eef31b/en-US)
 * [Using an AWS CloudFormation Stack to Create a Neptune DB Cluster](https://docs.aws.amazon.com/neptune/latest/userguide/get-started-cfn-create.html)
 * [Use Neptune graph notebooks to get started quickly](https://docs.aws.amazon.com/neptune/latest/userguide/graph-notebooks.html)
 * [(GitHub) amazon-neptune-samples](https://github.com/aws-samples/amazon-neptune-samples/)
 * [(GitHub) aws/graph-notebook](https://github.com/aws/graph-notebook)
