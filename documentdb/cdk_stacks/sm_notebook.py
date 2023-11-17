#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,

  aws_ec2,
  aws_iam,
  aws_sagemaker
)
from constructs import Construct


class SageMakerNotebookStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, docdb_cluster, sg_docdb_client, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sagemaker_notebook_role_policy_doc = aws_iam.PolicyDocument()
    sagemaker_notebook_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [docdb_cluster.secret.secret_full_arn],
      "actions": ["secretsmanager:GetSecretValue"]
    }))

    sagemaker_notebook_role = aws_iam.Role(self, 'SageMakerNotebookRoleForDocDB',
      role_name='AWSSageMakerNotebookRoleForDocDB',
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      inline_policies={
        'DocumentDBSecretPolicy': sagemaker_notebook_role_policy_doc
      }
    )

    docdb_wb_lifecycle_content = '''#!/bin/bash
sudo -u ec2-user -i <<'EOF'
echo "export AWS_REGION={AWS_Region}" >> ~/.bashrc
source /home/ec2-user/anaconda3/bin/activate python3
pip install --upgrade pymongo
pip install --upgrade xgboost
source /home/ec2-user/anaconda3/bin/deactivate
cd /home/ec2-user/SageMaker
wget https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem
wget https://raw.githubusercontent.com/aws-samples/documentdb-sagemaker-example/main/script.ipynb
EOF
'''.format(AWS_Region=cdk.Aws.REGION)

    docdb_wb_lifecycle_config_prop = aws_sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
      content=cdk.Fn.base64(docdb_wb_lifecycle_content)
    )

    docdb_wb_lifecycle_config = aws_sagemaker.CfnNotebookInstanceLifecycleConfig(self, 'DocDBWorkbenchLifeCycleConfig',
      notebook_instance_lifecycle_config_name='DocDBWorkbenchLifeCycleConfig',
      on_start=[docdb_wb_lifecycle_config_prop]
    )

    docdb_workbench = aws_sagemaker.CfnNotebookInstance(self, 'DocDBWorkbench',
      instance_type='ml.t3.xlarge',
      role_arn=sagemaker_notebook_role.role_arn,
      lifecycle_config_name=docdb_wb_lifecycle_config.notebook_instance_lifecycle_config_name,
      notebook_instance_name='DocDBWorkbench',
      root_access='Disabled',
      security_group_ids=[sg_docdb_client.security_group_id],
      subnet_id=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids[0]
    )

    cdk.CfnOutput(self, 'SageMakerRole',
      value=sagemaker_notebook_role.role_name,
      export_name=f'{self.stack_name}-SageMakerRole')
    cdk.CfnOutput(self, 'SageMakerNotebookInstance',
      value=docdb_workbench.notebook_instance_name,
      export_name=f'{self.stack_name}-SageMakerNotebookInstance')
    cdk.CfnOutput(self, 'SageMakerNotebookInstanceLifecycleConfig',
      value=docdb_workbench.lifecycle_config_name,
      export_name=f'{self.stack_name}-SageMakerNotebookInstanceLifecycleConfig')
