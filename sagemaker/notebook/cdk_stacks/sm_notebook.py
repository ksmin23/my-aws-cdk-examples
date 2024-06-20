#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_sagemaker
)
from constructs import Construct


class SageMakerNotebookStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    SAGEMAKER_NOTEBOOK_INSTANCE_TYPE = cdk.CfnParameter(self, 'SageMakerNotebookInstanceType',
      type='String',
      description='Amazon SageMaker Notebook instance type',
      default='ml.t2.medium'
    )

    sg_sagemaker_notebook_instance = aws_ec2.SecurityGroup(self, "SageMakerNotebookSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='Security group with no ingress rule',
      security_group_name=f'sagemaker-nb-{self.stack_name}-sg'
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

    sagemaker_notebook_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeImages",
        "ecr:DescribeRepositories",
        "ecr:GetDownloadUrlForLayer",
        "ecr:InitiateLayerUpload",
        "ecr:ListImages",
        "ecr:PutImage",
        "ecr:UploadLayerPart",
        "ecr:CreateRepository",
        "ecr:GetAuthorizationToken",
        "ec2:DescribeAvailabilityZones"
      ]
    }))

    sagemaker_mlflow_policy_doc = aws_iam.PolicyDocument()
    sagemaker_mlflow_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "sagemaker-mlflow:*"
      ]
    }))

    sagemaker_notebook_role = aws_iam.Role(self, 'SageMakerNotebookRole',
      role_name=f'SageMakerNotebookRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      inline_policies={
        'sagemaker-custome-execution-role': sagemaker_notebook_role_policy_doc,
        'sagemaker-mlflow-policy': sagemaker_mlflow_policy_doc,
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

# You can list all discoverable environments with `conda info --envs`.
for each in python3
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
      notebook_instance_lifecycle_config_name=f'{self.stack_name}-NotebookLCC',
      on_start=[sagemaker_lifecycle_config_prop]
    )

    sagemaker_notebook_instance = aws_sagemaker.CfnNotebookInstance(self, 'SageMakerNotebookInstance',
      instance_type=SAGEMAKER_NOTEBOOK_INSTANCE_TYPE.value_as_string,
      role_arn=sagemaker_notebook_role.role_arn,
      lifecycle_config_name=sagemaker_lifecycle_config.notebook_instance_lifecycle_config_name,
      notebook_instance_name='MySageMakerWorkbook',
      platform_identifier="notebook-al2-v2", # JupyterLab3
      root_access='Enabled', # To use local mode, set root access enabled
      security_group_ids=[sg_sagemaker_notebook_instance.security_group_id],
      # subnet_id=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids[0]
      subnet_id=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PUBLIC).subnet_ids[0],
      volume_size_in_gb=100 # 100GB, default: 5GB
    )

    cdk.CfnOutput(self, 'SageMakerNotebookInstanceName', value=sagemaker_notebook_instance.notebook_instance_name,
      export_name=f'{self.stack_name}-NotebookInstanceName')
