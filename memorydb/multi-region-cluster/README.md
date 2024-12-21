
# Amazon MemoryDB Multi-Region Cluster

![amazon-memorydb-multi-region-cluster](./amazon-memorydb-multi-region-cluster.svg)

This is a CDK Python project for Amazon MemoryDB Multi-Region cluster.

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

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

#### Step 1) Multi-Region cluster settings

Before synthesizing the CloudFormation, you should set approperly the cdk context configuration file, `cdk.context.json`.

For example:

<pre>
{
  "memorydb_mlti_region_cluster": {
    "node_type": "db.r7g.xlarge",
    "engine": "Valkey",
    "engine_version": "7.3",
    "multi_region_cluster_name_suffix": "mrc-demo",
    "num_shards": 3
  }
}
</pre>

At this point you can now synthesize the CloudFormation template for this code.

```
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all
```

Now we will be able to deploy all the CDK stacks at once like this:

```
(.venv) $ cdk deploy --require-approval never --all
```

#### Step 2) Region 1 cluster setting

Create the Regional cluster within your Multi-Region cluster with the appropriate cluster settings.

<pre>
(.venv) $ MULTI_REGION_CLUSTER_NAME=$(aws cloudformation describe-stacks --stack-name <i>MemoryDBMultiRegionClusterStack</i> \
| jq -r '.Stacks[0].Outputs | map(select(.OutputKey == "MemDBMultiRegionClusterName")) | .[0].OutputValue')
(.venv) cd ../valkey-cluster
(.venv) cdk deploy \
            -c memorydb_multi_region_cluster_name=${MULTI_REGION_CLUSTER_NAME} \
            --require-approval never --all
</pre>

#### Step 3) Region 2 cluster setting

You can add a second Regional cluster to your Multi-Region cluster after the Multi-Region cluster and the first Regional cluster are set up.

First, change the default region of your aws account to a second region (e.g., `us-west-2`) where you deploy a second memorydb cluster like this:
<pre>
(.venv) aws configure set region <i>us-west-2</i>
</pre>

Then deploy the cdk stacks for the second memorydb cluster to the second region.
<pre>
(.venv) cdk deploy \
            -c memorydb_multi_region_cluster_name=${MULTI_REGION_CLUSTER_NAME} \
            --require-approval never --all
</pre>

## Clean Up

The process of deleting a memorydb multi-region cluster involves reversing the steps taken during its creation. This cleanup procedure consists of three main steps:

#### Step 1) Remove Region 2 cluster

To delete the cluster in the second region:

1. Navigate to the `valkey-cluster` directory.
2. Verify that the AWS CLI is configured for the `us-west-2` region.
3. Execute the CDK destroy command:
   <pre>
   (.venv) basename $(pwd)
   valkey-cluster
   (.venv) aws configure get region
   us-west-2
   (.venv) cdk destroy --force --all
   </pre>

#### Step 2) Remove Region 1 cluster

For deleting the cluster in the first region:

1. Ensure you're still in the `valkey-cluster` directory.
2. Set the AWS CLI region to your default CDK region.
3. Run the CDK destroy command:
   <pre>
   (.venv) basename $(pwd)
   valkey-cluster
   (.venv) aws configure set region <i>${CDK_DEFAULT_REGION}</i>
   (.venv) cdk destroy --force --all
   </pre>

#### Step 3) Remove Multi-Region cluster

After removing both regional clusters, proceed to delete the multi-region cluster setup.

1. Navigate to the `multi-region-cluster` directory.
2. Execute the CDK destroy command:
   <pre>
   (.venv) cd ../multi-region-cluster
   (.venv) basename $(pwd)
   multi-region-cluster
   (.venv) cdk destroy --force --all
   </pre>

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## Considerations

 * [MemoryDB Multi-Region - Prerequisites and limitations](https://docs.aws.amazon.com/memorydb/latest/devguide/multi-region.prereq.html)
 * [MemoryDB Multi-Region - Supported and unsupported commands](https://docs.aws.amazon.com/memorydb/latest/devguide/multi-Region.SupportedCommands.html)

## References

 * [(AWS Blog) Amazon MemoryDB Multi-Region is now generally available (2024-12-01)](https://aws.amazon.com/blogs/aws/amazon-memorydb-multi-region-is-now-generally-available/)
