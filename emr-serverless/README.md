
# Amazon EMR Serverless CDK Python project!

This is an Amazon EMR Serverless project for CDK development with Python.

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

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ cdk synth --parameters EMRServerlessAppName="<i>your-emr-serverless-application-name</i>"
</pre>

Use cdk `deploy command` to create the stack shown above.

<pre>
(.venv) $ cdk deploy --parameters EMRServerlessAppName="<i>your-emr-serverless-application-name</i>"
</pre>

If emr serverless application is successfully created, you can get detailed information about the application.

<pre>
(.venv) $ export APPLICATION_ID=$(aws emr-serverless list-applications | jq -r '.applications[] | select(.name=="<i>your-emr-serverless-application-name</i>") | .id')
(.venv) $ aws emr-serverless get-application --application-id $APPLICATION_ID
{
    "application": {
        "applicationId": "00f6bemq6vc36s09",
        "name": "<i>your-emr-serverless-application-name</i>",
        "arn": "arn:aws:emr-serverless:us-east-1:123456789012:/applications/00f6bemq6vc36s09",
        "releaseLabel": "emr-6.6.0",
        "type": "Spark",
        "state": "CREATED",
        "stateDetails": "Application created by user.",
        "initialCapacity": {
            "Driver": {
                "workerCount": 2,
                "workerConfiguration": {
                    "cpu": "2 vCPU",
                    "memory": "4 GB",
                    "disk": "20 GB"
                }
            },
            "Executor": {
                "workerCount": 10,
                "workerConfiguration": {
                    "cpu": "4 vCPU",
                    "memory": "8 GB",
                    "disk": "20 GB"
                }
            }
        },
        "maximumCapacity": {
            "cpu": "200 vCPU",
            "memory": "200 GB",
            "disk": "1000 GB"
        },
        "createdAt": "2022-12-15T23:16:09.674000+09:00",
        "updatedAt": "2022-12-15T23:16:09.674000+09:00",
        "tags": {},
        "autoStartConfiguration": {
            "enabled": true
        },
        "autoStopConfiguration": {
            "enabled": true,
            "idleTimeoutMinutes": 15
        },
        "architecture": "X86_64"
    }
}
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## Referencs

 * [Getting started with Amazon EMR Serverless](https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/getting-started.html)
 * [Amazon EMR Serverless Release versions](https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/release-versions.html)
 * [Amazon EMR Best Practices Guides](https://aws.github.io/aws-emr-best-practices/)
 * [Tutorials for EMR Serverless](https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/tutorials.html)
 * :movie_camera: [Amazon EMR Serverless로 시작하는 쉬운 빅데이터 분석](https://youtu.be/TZHnLhCqdNg)

