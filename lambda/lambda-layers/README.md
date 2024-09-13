
# AWS Lambda Layer CDK Python project!

This is a project for Lambda Layer CDK development with Python.

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

Before synthesizing the CloudFormation, **you first create a python package to regisiter with AWS Lambda Layer.
Then you upload the python package into S3 (e.g., <i>s3-bucket-lambda-layer-lib</i>)**

For more information about how to create a python package for AWS Lambda Layer, see [References](#references).

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all \
              -c vpc_name=<i>your-existing-vpc-name</i> \
              -c s3_bucket_lambda_layer_lib=<i>s3-bucket-lambda-layer-lib</i>
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy --require-approval never --all \
              -c vpc_name=<i>your-existing-vpc-name</i> \
              -c s3_bucket_lambda_layer_lib=<i>s3-bucket-lambda-layer-lib</i>
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

+ [AWS Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html#configuration-layers-path)
    + How to create a python package to register with AWS Lambda layer (e.g., **elasticsearch**, **pytz**) on **Amazon Linux**

      :warning: **You should create the python package on Amazon Linux, otherwise create it using a simulated Lambda environment with Docker.**
      <pre>
      $ python3 -m venv es-lib
      $ cd es-lib
      $ source bin/activate
      (es-lib) $ mkdir -p python_modules
      (es-lib) $ pip install 'elasticsearch>=7.0.0,< 7.11' pytz==2022.1 -t python_modules
      (es-lib) $ mv python_modules python
      (es-lib) $ zip -r es-lib.zip python/
      (es-lib) $ aws s3 mb s3://my-bucket-for-lambda-layer-packages
      (es-lib) $ aws s3 cp es-lib.zip s3://my-bucket-for-lambda-layer-packages/var/
      (es-lib) $ deactivate
      </pre>
    + [How to create a Lambda layer using a simulated Lambda environment with Docker](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-simulated-docker/)
      <pre>
      $ cat <<EOF > requirements.txt
      > elasticsearch>=7.0.0,<7.11
      > pytz==2022.1
      > EOF
      $ docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.7" /bin/sh -c "pip install -r requirements.txt -t python/lib/python3.7/site-packages/; exit"
      $ zip -r es-lib.zip python > /dev/null
      $ aws s3 mb s3://my-bucket-for-lambda-layer-packages
      $ aws s3 cp es-lib.zip s3://my-bucket-for-lambda-layer-packages/var/
      </pre>

