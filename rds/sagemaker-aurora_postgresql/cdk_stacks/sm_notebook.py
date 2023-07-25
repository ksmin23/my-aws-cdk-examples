#!/usr/bin/env python3
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

  def __init__(self, scope: Construct, construct_id: str, vpc, sg_rds_client, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sg_sagemaker_nb = aws_ec2.SecurityGroup(self, 'SageMakerNotebookSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for sagmaker notebook instances',
      security_group_name='sagemaker-nb-sg'
    )
    sg_sagemaker_nb.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"), connection=aws_ec2.Port.tcp(443),
      description='https')
    cdk.Tags.of(sg_sagemaker_nb).add('Name', 'sagemaker-nb-sg')

    sagemaker_notebook_role_policy_doc = aws_iam.PolicyDocument()
    sagemaker_notebook_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": ["secretsmanager:GetSecretValue"]
    }))

    sagemaker_notebook_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:s3:::sagemaker-*"],
      "actions": ["s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"]
    }))

    sagemaker_notebook_role = aws_iam.Role(self, 'SageMakerNotebookRoleForRDS',
      role_name='AWSSageMakerNotebookRoleForRDS',
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      inline_policies={
        'sagemaker-nb-custom-policy': sagemaker_notebook_role_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerFullAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AWSCloudFormationReadOnlyAccess')
      ]
    )

    cf_readonly_access_policy = aws_iam.ManagedPolicy.from_aws_managed_policy_name('AWSCloudFormationReadOnlyAccess')
    sagemaker_notebook_role.add_managed_policy(cf_readonly_access_policy) 

    #XXX: skip downloading rds-combined-ca-bundle.pem if not use SSL with a MySQL DB instance
    # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_MySQL.html#MySQL.Concepts.SSLSupport
    rds_wb_lifecycle_content = '''#!/bin/bash
sudo -u ec2-user -i <<'EOF'
echo "export AWS_REGION={AWS_Region}" >> ~/.bashrc
source /home/ec2-user/anaconda3/bin/activate python3
pip install --upgrade ipython-sql
pip install --upgrade psycopg2-binary
pip install --upgrade pretty_errors
source /home/ec2-user/anaconda3/bin/deactivate
cd /home/ec2-user/SageMaker
wget -N https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem
wget -N https://raw.githubusercontent.com/ksmin23/my-aws-cdk-examples/main/rds/sagemaker-aurora_postgresql/ipython-sql-postgresql.ipynb
EOF
'''.format(AWS_Region=cdk.Aws.REGION)

    rds_wb_lifecycle_config_prop = aws_sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
      content=cdk.Fn.base64(rds_wb_lifecycle_content)
    )

    rds_wb_lifecycle_config = aws_sagemaker.CfnNotebookInstanceLifecycleConfig(self, 'PgSQLWorkbenchLifeCycleConfig',
      notebook_instance_lifecycle_config_name='PgSQLWorkbenchLifeCycleConfig',
      on_start=[rds_wb_lifecycle_config_prop]
    )

    rds_workbench = aws_sagemaker.CfnNotebookInstance(self, 'AuroraPostgreSQLWorkbench',
      instance_type='ml.t3.xlarge',
      role_arn=sagemaker_notebook_role.role_arn,
      lifecycle_config_name=rds_wb_lifecycle_config.notebook_instance_lifecycle_config_name,
      notebook_instance_name='AuroraPostgreSQLWorkbench',
      root_access='Disabled',
      security_group_ids=[sg_sagemaker_nb.security_group_id, sg_rds_client.security_group_id],
      subnet_id=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids[0],
      volume_size_in_gb=20
    )

    cdk.CfnOutput(self, 'SageMakerRole', value=sagemaker_notebook_role.role_name, export_name='SageMakerRole')
    cdk.CfnOutput(self, 'SageMakerNotebookInstance', value=rds_workbench.notebook_instance_name,
      export_name='SageMakerNotebookInstance')
    cdk.CfnOutput(self, 'SageMakerNotebookInstanceLifecycleConfig', value=rds_workbench.lifecycle_config_name,
      export_name='SageMakerNotebookInstanceLifecycleConfig')
