
# Jenkins on Amazon EC2

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

```
(.venv) $ cdk synth 
```

If your VPC is created outside your CDK app, you can use `Vpc.fromLookup()`.
The CDK CLI will search for the specified VPC in the the stack’s region and account,
and import the subnet configuration.

To import an existing VPC, you should specify the following environment variables.

```
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
```

If you pass context variable such as `vcp_name=<your vpc name>` (e.g. `vpc_name='[X]default'`), you can use the existing VPC.

<pre>
(.venv) $ cdk synth -c vpc_name='[X]default' \
                    --parameters EC2KeyPairName="<i>your-ec2-key-pair-name(exclude .pem extension)</i>"
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy \
              --parameters EC2KeyPairName="<i>your-ec2-key-pair-name(exclude .pem extension)</i>"
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Configure Jenkins

This project installs Jenkins on an Amazon EC2 instance with the following Amazon Linux
<pre>
[ec2-user ~]$ cat /etc/*release
NAME="Amazon Linux"
VERSION="2"
ID="amzn"
ID_LIKE="centos rhel fedora"
VERSION_ID="2"
PRETTY_NAME="Amazon Linux 2"
ANSI_COLOR="0;33"
CPE_NAME="cpe:2.3:o:amazon:amazon_linux:2"
HOME_URL="https://amazonlinux.com/"
Amazon Linux release 2 (Karoo)
</pre>

Jenkins is now installed and running on your EC2 instance. To configure Jenkins:
 * Connect to http://<your_server_public_DNS>:80 from your favorite browser. You will be able to access Jenkins through its management interface:
   <div>
     <img src="./unlock_jenkins.png", alt with="800" height="465" />
   </div>
 * For more details, see [Tutorial for installing Jenkins on AWS](https://www.jenkins.io/doc/tutorials/tutorial-for-installing-jenkins-on-AWS/#configure-jenkins)

## Recommended Jenkins Plugins

| Plugin name | Version |
|-------------|---------|
| git | 4.10.2 |
| job-dsl | 1.78.3 |
| pipeline | 2.6 |
| pipeline-aws | 1.43 |
| CloudBees AWS Credentials for the Jenkins plugin | 1.33 |

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

 * [Tutorial for installing Jenkins on AWS](https://www.jenkins.io/doc/tutorials/tutorial-for-installing-jenkins-on-AWS/#configure-jenkins)
 * [AWS EC2에 Jenkins 설치하기 (2021-01-12)](https://velog.io/@yundleyundle/AWS-EC2%EC%97%90-Jenkins-%EC%84%A4%EC%B9%98%ED%95%98%EA%B8%B0)
 * [Create Amazon SageMaker projects using third-party source control and Jenkins (2021-08-17)](https://aws.amazon.com/blogs/machine-learning/create-amazon-sagemaker-projects-using-third-party-source-control-and-jenkins/)

