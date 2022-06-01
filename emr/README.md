
# Amazon EMR CDK Python project!

This is a blank project for Python development with CDK.

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
You pass context variable such as `vcp_name=<your vpc name>` (e.g. `vpc_name='default'`) in order to use the existing VPC.

<pre>
(.venv) $ cdk synth -c vpc_name="<i>your-vpc-name</i>" \
              --parameters EMREC2KeyPairName="<i>your-emr-ec2-key-pair-name(exclude .pem extension)</i>"
</pre>

Before deployment, you shuld create the default IAM role `EMR_EC2_DefaultRole` and `EMR_DefaultRole` which can be used when creating the cluster

```
(.venv) $ aws emr create-default-roles
```

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy -c vpc_name="<i>your-vpc-name</i>" \
              --parameters EMREC2KeyPairName="<i>your-emr-ec2-key-pair-name(exclude .pem extension)</i>"
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Clean up

Before cleaning up the emr cluster, you need to tunrn off EMR `Termination protection`.

<pre>
(.venv) $ aws emr modify-cluster-attributes --cluster-id <i>your-emr-cluster-id</i> --no-termination-protected
(.venv) $ cdk destroy --force
</pre>

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

## References

 * [Application versions in Amazon EMR 6.x releases](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-release-app-versions-6.x.html)
 * [Application versions in Amazon EMR 5.x releases](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-release-app-versions-5.x.html)
 * [aws emr create-default-roles](https://docs.aws.amazon.com/cli/latest/reference/emr/create-default-roles.html)
 * [When I create an Amazon EMR cluster, I get an "EMR_DefaultRole is invalid" or "EMR_EC2_DefaultRole is invalid" error](https://aws.amazon.com/premiumsupport/knowledge-center/emr-default-role-invalid/)

Enjoy!
