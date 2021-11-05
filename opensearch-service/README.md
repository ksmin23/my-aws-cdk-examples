
# Amazon OpenSearch Service

![amazon-opensearch-arch](./amazon-opensearch-arch.svg)

This is a project for Python development with CDK.

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
(.venv) $ cdk synth \
              --parameters OpenSearchDomainName="<i>your-opensearch-domain-name</i>"
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy \
              --parameters OpenSearchDomainName="<i>your-opensearch-domain-name</i>"
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

## Remotely access your Amazon OpenSearch Cluster using SSH tunnel from local machine
1. Generate the new private and public keys `mynew_key` and `mynew_key.pub`, respectively:

   ```
   $ ssh-keygen -t rsa -f mynew_key
   ```

2. To access the OpenSearch Cluster, add the ssh tunnel configuration to the ssh config file of the personal local PC as follows

    <pre>
    # OpenSearch Tunnel
    Host osstunnel
        HostName <i>EC2-Public-IP-of-Bastion-Host</i>
        User ec2-user
        IdentitiesOnly yes
        IdentityFile <i>Path-to-SSH-Public-Key</i>
        LocalForward 9200 <i>OpenSearch-Endpoint</i>:443
    </pre>

    ex)

    ```
    ~$ ls -1 .ssh/
    config
    mynew_key
    mynew_key.pub

    ~$ tail .ssh/config
    # OpenSearch Tunnel
    Host osstunnel
        HostName 214.132.71.219
        User ec2-user
        IdentitiesOnly yes
        IdentityFile ~/.ssh/mynew_key.pub
        LocalForward 9200 vpc-oss-hol-qvwlxanar255vswqna37p2l2cy.us-east-1.es.amazonaws.com:443

    ~$
    ```

3. Use the following AWS CLI command to authorize the user and push the public key to the instance using the send-ssh-public-key command. To support this, you need the latest version of the AWS CLI.

   ex) Bastion Host's instance details
   - Instance ID: `i-0989ec3292613a4f9`
   - Availability Zone: `us-east-1a`
   - Instance OS User: `ec2-user`

   ```
   $ aws ec2-instance-connect send-ssh-public-key --region us-east-1 --instance-id i-0989ec3292613a4f9 --availability-zone us-east-1a --instance-os-user ec2-user --ssh-public-key file://${HOME}/.ssh/mynew_key.pub
   {
     "RequestId": "505f8675-710a-11e9-9263-4d440e7745c6",
     "Success": true
   } 
   ```

4. Run `ssh -N estunnel` in Terminal.
5. Connect to `https://localhost:9200/_dashboards/` in a web browser.
6. If you would like to access the OpenSearch Cluster in a termial, open another terminal window, and then run the following commands: (in here, <i>`your-cloudformation-stack-name`</i> is `OpensearchStack`)

    <pre>
    $ MASTER_USER_SECRET_ID=$(aws cloudformation describe-stacks --stack-name <i>your-clouformation-stack-name</i> | jq -r '.Stacks[0].Outputs | map(select(.OutputKey == "MasterUserSecretId")) | .[0].OutputValue')
    $ export OSS_SECRETS=$(aws secretsmanager get-secret-value --secret-id ${MASTER_USER_SECRET_ID} | jq -r '.SecretString | fromjson | "\(.username):\(.password)"')
    $ export OSS_DOMAIN=$(aws cloudformation describe-stacks --stack-name OpensearchStack | jq -r '.Stacks[0].Outputs | map(select(.OutputKey == "OpenSearchDomainEndpoint")) | .[0].OutputValue')
    $ curl -XGET --insecure -u "${OSS_SECRETS}" https://localhost:9200/_cluster/health?pretty=true
    $ curl -XGET --insecure -u "${OSS_SECRETS}" https://localhost:9200/_cat/nodes?v
    $ curl -XGET --insecure -u "${OSS_SECRETS}" https://localhost:9200/_nodes/stats?pretty=true
    </pre>

#### References
- [Windows SSH / Tunnel for Kibana Instructions - Amazon Elasticsearch Service](https://search-sa-log-solutions.s3-us-east-2.amazonaws.com/logstash/docs/Kibana_Proxy_SSH_Tunneling_Windows.pdf)
- [Use an SSH Tunnel to access Kibana within an AWS VPC with PuTTy on Windows](https://amazonmsk-labs.workshop.aws/en/mskkdaflinklab/createesdashboard.html)
- [OpenSearch Popular APIs](https://opensearch.org/docs/latest/opensearch/popular-api/)
