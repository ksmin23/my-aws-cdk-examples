
# Creating Jupyter Notebook Server using Amazon Deep Learning AMI (DLAMI)

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

Before to synthesize the CloudFormation template for this code, you should update `cdk.context.json` file.

For example,

<pre>
{
  "jupyter_notebook_instance_type": "g4dn.2xlarge",
  "dlami_name": "Deep Learning Proprietary Nvidia Driver AMI GPU PyTorch 2.0.1 (Amazon Linux 2) 20240206",
  "vpc_name": "default",
  "ec2_key_pair_name": "<i>your-ec2-key-pair-name(exclude .pem extension)</i>",
  "jupyter_password": "<i>your-password</i>"
}
</pre>

Now you are ready to synthesize the CloudFormation template for this code.

<pre>
(.venv) $ cdk synth --all
</pre>

> :information_source: You can find out the latest Deep learning AMI by runing the following command:
   <pre>
     aws ec2 describe-images --region <i>us-east-1</i> \
         --owners amazon \
         --filters 'Name=name,Values=Deep Learning Proprietary Nvidia Driver AMI GPU PyTorch 2.0.1 (Amazon Linux 2) ????????' 'Name=state,Values=available' \
         --query 'reverse(sort_by(Images, &CreationDate))[:1].Name'
   </pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy --all
</pre>

Or, we can provision each CDK stack one at a time like this:

```
(.venv) $ cdk list
JupyterOnDLAMIVpcStack
JupyterOnDLAMIStack

(.venv) $ cdk deploy JupyterOnDLAMIVpcStack

(.venv) $ cdk deploy JupyterOnDLAMIStack
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Logging in to the Jupyter notebook server

1. Find out the Jupyter notebook server endpoint by running the following command:
   ```
   $ aws cloudformation describe-stacks \
        --stack-name JupyterOnDLAMIStack | \
        jq -r '.Stacks[0].Outputs | .[] | select(.OutputKey | endswith("JupyterURL")) | .OutputValue'
   ```
2. In the address bar of your browser, type the URL above, or click on the link<br/>
   Because the Jupyter server is configured with a self-signed SSL certificate, your browser warns you and prompts you to avoid continuing to this website. But because you set this up yourself, it’s safe to continue.

   - (Step 1) Choose **Advanced**.
   - (Step 2) Choose **Proceed**.
   - (Step 3) Use the password `your-password` to log in.

   For more information, see [AWS Deep Learning AMI - Test by Logging in to the Jupyter notebook server](https://docs.aws.amazon.com/dlami/latest/devguide/setup-jupyter-login.html)


## Clean Up

Delete the CloudFormation stacks by running the below command.

```
(.venv) $ cdk destroy --all
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

 * [Release Notes for Amazon DLAMI](https://docs.aws.amazon.com/dlami/latest/devguide/appendix-ami-release-notes.html)
   * Query AMI-ID with AWSCLI (example region is `us-east-1`):
     <pre>
     aws ec2 describe-images --region us-east-1 \
         --owners amazon \
         --filters 'Name=name,Values=Deep Learning AMI (Amazon Linux 2) Version ??.?' 'Name=state,Values=available' \
         --query 'reverse(sort_by(Images, &CreationDate))[:1].Name'
     </pre>
 * [Deep Learning AMI - Set up a Jupyter Notebook Server](https://docs.aws.amazon.com/dlami/latest/devguide/setup-jupyter.html)
 * [Running a jupyter notebook server](https://jupyter-notebook.readthedocs.io/en/stable/public_server.html)
 * [Starting JupyterLab](https://jupyterlab.readthedocs.io/en/stable/getting_started/starting.html)
 * [How to Import and Export a Client Personal Authentication Certificate on Mac OS X Keychain Access](https://sectigo.com/faqs/detail/How-to-Import-and-Export-a-Client-Personal-Authentication-Certificate-on-Mac-OS-X-Keychain-Access/kA03l000000vFhu)
 * [Preparing data for ML models using AWS Glue DataBrew in a Jupyter notebook](https://aws.amazon.com/blogs/big-data/preparing-data-for-ml-models-using-aws-glue-databrew-in-a-jupyter-notebook/)
   * [AWS Glue Databrew Jupyter extension Github Repository](https://github.com/aws/aws-glue-databrew-jupyter-extension/tree/main/blogpost/cloudformation)
 * [How can I send user-data output to the console logs on an EC2 instance running Amazon Linux or Amazon Linux 2?](https://aws.amazon.com/premiumsupport/knowledge-center/ec2-linux-log-user-data/)
   * The following is the line that redirects the user-data output:
     ```
     exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
     ```

