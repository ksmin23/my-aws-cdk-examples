
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
(.venv) $ cdk synth --all \
              -c OpenSearchDomainName="<i>your-opensearch-domain-name</i>" \
              -c EC2KeyPairName="<i>your-ec2-key-pair-name(exclude .pem extension)</i>"
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy --all \
              -c OpenSearchDomainName="<i>your-opensearch-domain-name</i>" \
              -c EC2KeyPairName="<i>your-ec2-key-pair-name(exclude .pem extension)</i>"
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

### A note about Service-Linked Role
Some cluster configurations (e.g VPC access) require the existence of the `AWSServiceRoleForAmazonOpenSearchService` Service-Linked Role.

When performing such operations via the AWS Console, this SLR is created automatically when needed. However, this is not the behavior when using CloudFormation. If an SLR(Service-Linked Role) is needed, but doesn’t exist, you will encounter a failure message simlar to:

<pre>
Before you can proceed, you must enable a service-linked role to give Amazon OpenSearch Service...
</pre>

To resolve this, you need to [create](https://docs.aws.amazon.com/IAM/latest/UserGuide/using-service-linked-roles.html#create-service-linked-role) the SLR. We recommend using the AWS CLI:

```
aws iam create-service-linked-role --aws-service-name opensearchservice.amazonaws.com
```

:information_source: For more information, see [here](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/slr.html).

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

## Remotely access your Amazon OpenSearch Cluster using SSH tunnel from local machine
1. The Amazon OpenSearch cluster is provisioned in a VPC. Hence, the Amazon OpenSearch endpoint and dashboard are not available over the internet. In order to access the endpoints, we have to create a ssh tunnel and do local port forwarding.
   1. **using SSH tunnel**
      1. To access the OpenSearch Cluster, add the ssh tunnel configuration to the ssh config file of the personal local PC as follows

         <pre>
         # OpenSearch Tunnel
         Host opstunnel
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
         my-ec2-key-pair.pem

         ~$ tail .ssh/config
         # OpenSearch Tunnel
         Host opstunnel
             HostName 214.132.71.219
             User ec2-user
             IdentitiesOnly yes
             IdentityFile ~/.ssh/my-ec2-key-pair.pem
             LocalForward 9200 vpc-search-domain-qvwlxanar255vswqna37p2l2cy.us-east-1.es.amazonaws.com:443

         ~$
         ```

         You can find the bastion host's public ip address as running the commands like this:

         <pre>
         $ BASTION_HOST_ID=$(aws cloudformation describe-stacks --stack-name <i>your-cloudformation-stack-name</i> | jq -r '.Stacks[0].Outputs | map(select(.OutputKey == "BastionHostBastionHostId")) | .[0].OutputValue')
         $ aws ec2 describe-instances --instance-ids ${BASTION_HOST_ID} | jq -r '.Reservations[0].Instances[0].PublicIpAddress'
         </pre>

      2. Run `ssh -N opstunnel` in Terminal.
   2. **using EC2 Instance Connect CLI** (`mssh`)
      1. Install EC2 Instance Connect CLI
         ```
         sudo pip install ec2instanceconnectcli
         ```
      2. Run
         <pre>mssh --region {<i>region</i>} ec2-user@{<i>bastion-ec2-instance-id</i>} -N -L 9200:{<i>opensearch-endpoint</i>}:443</pre>
         + ex)
         ```
         $ mssh --region us-east-1 ec2-user@i-0203f0d6f37ccbe5b -N -L 9200:vpc-retail-qvwlxanar255vswqna37p2l2cy.us-east-1.es.amazonaws.com:443
         ```
2. Connect to `https://localhost:9200/_dashboards/app/login?` in a web browser.
3. Enter the master user and password that you set up when you created the Amazon OpenSearch Service endpoint. The user and password are stored in the [AWS Secrets Manager](https://console.aws.amazon.com/secretsmanager/listsecrets) as a name such as `OpenSearchMasterUserSecret1-xxxxxxxxxxxx`.
4. In the Welcome screen, click the toolbar icon to the left side of **Home** button. Choose **Stack Managerment**
   ![ops-dashboards-sidebar-menu](./resources/ops-dashboards-sidebar-menu.png)
5. After selecting **Advanced Settings** from the left sidebar menu, set **Timezone** for date formatting to `Etc/UTC`.
   Since the log creation time of the test data is based on UTC, OpenSearch Dashboard’s Timezone is also set to UTC.
   ![ops-dashboards-stack-management-advanced-setting.png](./resources/ops-dashboards-stack-management-advanced-setting.png)
6. If you would like to access the OpenSearch Cluster in a termial, open another terminal window, and then run the following commands: (in here, <i>`your-cloudformation-stack-name`</i> is `OpensearchStack`)

    <pre>
    $ MASTER_USER_SECRET_ID=$(aws cloudformation describe-stacks --stack-name <i>your-cloudformation-stack-name</i> | jq -r '.Stacks[0].Outputs | map(select(.OutputKey == "MasterUserSecretId")) | .[0].OutputValue')
    $ export OPS_SECRETS=$(aws secretsmanager get-secret-value --secret-id ${MASTER_USER_SECRET_ID} | jq -r '.SecretString | fromjson | "\(.username):\(.password)"')
    $ export OPS_DOMAIN=$(aws cloudformation describe-stacks --stack-name <i>your-cloudformation-stack-name</i> | jq -r '.Stacks[0].Outputs | map(select(.OutputKey == "OpenSearchDomainEndpoint")) | .[0].OutputValue')
    $ curl -XGET --insecure -u "${OPS_SECRETS}" https://localhost:9200/_cluster/health?pretty=true
    $ curl -XGET --insecure -u "${OPS_SECRETS}" https://localhost:9200/_cat/nodes?v
    $ curl -XGET --insecure -u "${OPS_SECRETS}" https://localhost:9200/_nodes/stats?pretty=true
    </pre>

#### References

- [Operational best practices for Amazon OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/bp.html)
  - [Sizing Amazon OpenSearch Service domains](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/sizing-domains.html)
  - [동작 방식과 함께 알아보는 최적의 Amazon OpenSearch Service 사이징 (2024-04-26)](https://aws.amazon.com/ko/blogs/tech/opensearch-sizing/)
- [Windows SSH / Tunnel for Kibana Instructions - Amazon Elasticsearch Service](https://search-sa-log-solutions.s3-us-east-2.amazonaws.com/logstash/docs/Kibana_Proxy_SSH_Tunneling_Windows.pdf)
- [Use an SSH Tunnel to access Kibana within an AWS VPC with PuTTy on Windows](https://amazonmsk-labs.workshop.aws/en/mskkdaflinklab/createesdashboard.html)
- [OpenSearch Popular APIs](https://opensearch.org/docs/latest/opensearch/popular-api/)
- [Amazon OpenSearch Plugins by engine version](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/supported-plugins.html)
- [Supported versions of OpenSearch and Elasticsearch](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/what-is.html#choosing-version)
- [Supported instance types in Amazon OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/supported-instance-types.html#latest-gen)
- [Connect using the EC2 Instance Connect CLI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-methods.html#ec2-instance-connect-connecting-ec2-cli)
   <pre>
   $ sudo pip install ec2instanceconnectcli
   $ mssh --region us-east-1 ec2-user@i-001234a4bf70dec41EXAMPLE
   </pre>

#### Known Issues
- [(aws-elasticsearch): Vpc.fromLookup returns dummy VPC if the L2 elasticsearch.Domain availabilityZoneCount is set to 3](https://github.com/aws/aws-cdk/issues/12078)
  - **What did you expect to happen?**
    The lookup should find the VPC and populate the `cdk.context.json`. The synth should successfully show the resource template with the correct subnets and values.
  - **What actually happened?**
    An error is thrown, "When providing vpc options you need to provide a subnet for each AZ you are using" due to the VPC lookup silently failing and instead giving dummy data.
  - **How to work around this problem**
    > To work around this problem for now, you can temporarily remove the `Domain` definition from the application, run `cdk synth`, and then put it back in. This first `synth` will query the actual VPC details and store them in the `cdk.context.json` file, which will be used from now on, so that the dummy VPC will not be used.
    > (davidhessler@ commented on 29 Dec 2020)

