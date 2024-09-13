
# AWS Lambda Asynchronous Invocation

![aws-lambda-async-invocation](./aws-lambda-async-invocation.svg)

This is a example of AWS Lambda Asynchronous Invocation with Python CDK.

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
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all
```

Use `cdk deploy` command to create the stack shown above.

```
(.venv) $ cdk deploy --all
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

### Verify

If you want to test asychronous lambda invocation, run `send_sns.py` script on the EC2 instance by entering the following command:

```
(.venv) $ cd ..
(.venv) $ ls src/utils/
send_sns.py
(.venv) $ python src/utils/send_sns.py # do asynchronous invocation on success
(.venv) $ python src/utils/send_sns.py --on-failure # do asynchronous invocation on failure
```

If you would like to know more about the usage of this command, you can type

<pre>
(.venv) $ python src/utils/send_sns.py --help
</pre>

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

## Gotchas

 * You *CANNOT* test destinations with the "Test" button in the AWS Web console, only CLI calls of the `Event` type.<br/>
   For example,
   ```
   aws lambda invoke \
      --function-name my-function \
      --invocation-type Event \
      --cli-binary-format raw-in-base64-out \
      --payload '{ "key": "value" }' response.json
   ```

## Learn more

 * [Introducing AWS Lambda Destinations](https://aws.amazon.com/blogs/compute/introducing-aws-lambda-destinations/)
 * [Understanding the Different Ways to Invoke Lambda Functions](https://aws.amazon.com/blogs/architecture/understanding-the-different-ways-to-invoke-lambda-functions/)
 * [Lambda Destinations: What We Learned the Hard Way](https://www.trek10.com/blog/lambda-destinations-what-we-learned-the-hard-way)
 * [Using AWS Lambda with other services](https://docs.aws.amazon.com/lambda/latest/dg/lambda-services.html)

Enjoy!
