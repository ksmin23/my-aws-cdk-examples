#!/usr/bin/env python3
import os
import random
import string

from aws_cdk import (
  core as cdk,
  aws_ec2,
  aws_iam,
  aws_s3 as s3,
  aws_sagemaker
)

random.seed(47)

class SageMakerNotebookStack(cdk.Stack):

  def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    SAGEMAKER_NOTEBOOK_INSTANCE_TYPE = cdk.CfnParameter(self, 'SageMakerNotebookInstanceType',
      type='String',
      description='Amazon SageMaker Notebook instance type',
      default='ml.t2.medium'
    )

    #XXX: For createing Amazon MWAA in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    vpc_name = self.node.try_get_context('vpc_name')
    vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
      is_default=True,
      vpc_name=vpc_name
    )

    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    # vpc = aws_ec2.Vpc(self, 'SageMakerStudioVPC',
    #   max_azs=2,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )

    sg_sagemaker_notebook_instance = aws_ec2.SecurityGroup(self, "SageMakerNotebookSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='Security group with no ingress rule',
      security_group_name='sagemaker-nb-{}-sg'.format(''.join(random.sample((string.ascii_letters), k=5)))
    )
    sg_sagemaker_notebook_instance.add_ingress_rule(peer=sg_sagemaker_notebook_instance, connection=aws_ec2.Port.all_traffic(), description='sagemaker notebook security group')
    cdk.Tags.of(sg_sagemaker_notebook_instance).add('Name', 'sagemaker-nb-sg')

    sagemaker_notebook_role_policy_doc = aws_iam.PolicyDocument()
    sagemaker_notebook_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:s3:::*"],
      "actions": ["s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"]
    }))

    sagemaker_notebook_role = aws_iam.Role(self, 'SageMakerNotebookRole',
      role_name='SageMakerNotebookRole-{suffix}'.format(suffix=''.join(random.sample((string.ascii_letters), k=5))),
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      inline_policies={
        'sagemaker-custome-execution-role': sagemaker_notebook_role_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerFullAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AWSCloudFormationReadOnlyAccess')
      ]
    )

    #XXX: skip downloading rds-combined-ca-bundle.pem if not use SSL with a MySQL DB instance
    # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_MySQL.html#MySQL.Concepts.SSLSupport
    sagemaker_nb_lifecycle_content = '''#!/bin/bash
sudo -u ec2-user -i <<'EOF'

echo "export AWS_REGION={AWS_Region}" >> ~/.bashrc
curl -LO https://bitbucket.org/eunjeon/mecab-ko/downloads/mecab-0.996-ko-0.9.2.tar.gz
tar zxfv mecab-0.996-ko-0.9.2.tar.gz
pushd mecab-0.996-ko-0.9.2
./configure
make
make check
sudo make install
sudo ldconfig
mecab -v
mecab-config --version
popd

curl -LO https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz
tar -zxvf mecab-ko-dic-2.1.1-20180720.tar.gz
pushd mecab-ko-dic-2.1.1-20180720
./autogen.sh
./configure
make
sudo make install
popd

for each in python3 pytorch_latest_p36
do
    source /home/ec2-user/anaconda3/bin/activate ${{each}}
    pip install --upgrade pretty_errors
    pip install --upgrade pandas-profiling[notebook]
    pip install --upgrade ipython-sql
    pip install --upgrade PyMySQL
    pip install torchvision
    pip install torchtext
    pip install spacy
    pip install nltk
    pip install requests
    pip install mecab-python
    pip install konlpy
    pip install jpype1-py3
    conda deactivate
done
EOF
'''.format(AWS_Region=cdk.Aws.REGION)

    sagemaker_lifecycle_config_prop = aws_sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
      content=cdk.Fn.base64(sagemaker_nb_lifecycle_content)
    )

    sagemaker_lifecycle_config = aws_sagemaker.CfnNotebookInstanceLifecycleConfig(self, 'SageMakerNotebookLifeCycleConfig',
      notebook_instance_lifecycle_config_name='SageMakerNotebookLifeCycleConfig',
      on_start=[sagemaker_lifecycle_config_prop]
    )

    sagemaker_notebook_instance = aws_sagemaker.CfnNotebookInstance(self, 'SageMakerNotebookInstance',
      instance_type=SAGEMAKER_NOTEBOOK_INSTANCE_TYPE.value_as_string,
      role_arn=sagemaker_notebook_role.role_arn,
      lifecycle_config_name=sagemaker_lifecycle_config.notebook_instance_lifecycle_config_name,
      notebook_instance_name='MySageMakerWorkbook',
      root_access='Disabled',
      security_group_ids=[sg_sagemaker_notebook_instance.security_group_id],
      subnet_id=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE).subnet_ids[0]
    )


app = cdk.App()
SageMakerNotebookStack(app, "SageMakerNotebookStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
