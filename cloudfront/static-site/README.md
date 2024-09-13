
# Amazon CloudFront CDK Python project!

![cloudfront-s3-static-site](./cloudfront-s3-static-site-arch.svg)

This example creates the infrastructure for a static site, which uses an S3 bucket for storing the content.

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

## Before you deploy
Before you deploy this project, you should create an Amazon S3 bucket to store your site contents.
The site contents (located in the 'site-contents' sub-directory) are deployed to the bucket.

For example,

<pre>
(.venv) $ aws s3 sync ./static-contents/ s3://<i>your-s3-bucket-for-static-content</i>/
</pre>

## Deploy

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth \
              --parameters S3BucketForStaticContents='<i>your-s3-bucket-for-static-contents</i>'
</pre>

If you generate a CloudFormation template based on our current CDK app, you would see the plain CloudFormation Parameters section:

<pre>
Parameters:
  S3BucketForStaticContents:
    Type: String
    Description: s3 bucket that the site contents are deployed to
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) cdk deploy \
            --parameters S3BucketForStaticContents='<i>your-s3-bucket-for-static-contents</i>'
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

## Learn more
 * [Static Site CDK Typescript example \(experimental\)](https://github.com/aws-samples/aws-cdk-examples/tree/master/typescript/static-site)
 * [Restricting access to Amazon S3 content by using an origin access identity \(OAI\)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)

Enjoy!
