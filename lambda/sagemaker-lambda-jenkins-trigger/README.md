
# Amazon Lambda for Jenkins Trigger

This CDK project creates Amazon Lambda function to trigger Jenkins job
when Amazon SageMaker Model package status changes.
(see the blue box in the following diagram)

<div>
  <img src="./sagemaker-lambda-jenkins-trigger.png", alt with="711" height="465" />
</div>

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
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth \
              --parameters JenkinsUser=<i>"Jenkins User"</i> \
              --parameters JenkinsAPIToken=<i>"JenkinsAPIToken"</i> \
              --parameters JenkinsUrl=<i>"http://jenkinshost"</i>
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy \
              --parameters JenkinsUser=<i>"Jenkins User"</i> \
              --parameters JenkinsAPIToken=<i>"JenkinsAPIToken"</i> \
              --parameters JenkinsUrl=<i>"http://jenkinshost"</i>
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Clean Up

Delete the CloudFormation stack by running the below command.

```
(.venv) $ cdk destroy
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

 * [Create Amazon SageMaker projects using third-party source control and Jenkins (2021-08-17)](https://aws.amazon.com/ko/blogs/machine-learning/create-amazon-sagemaker-projects-using-third-party-source-control-and-jenkins/)
