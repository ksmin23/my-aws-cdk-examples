#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_docdb,
  aws_sagemaker
)
from constructs import Construct


class DocumentdbStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # The code that defines your stack goes here
    vpc_name = self.node.try_get_context('vpc_name')
    vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
      is_default=True,
      vpc_name=vpc_name)

    sg_use_docdb = aws_ec2.SecurityGroup(self, 'DocDBClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for documentdb client',
      security_group_name='use-docdb-sg'
    )
    cdk.Tags.of(sg_use_docdb).add('Name', 'docdb-client-sg')

    sg_docdb_server = aws_ec2.SecurityGroup(self, 'DocDBServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for documentdb',
      security_group_name='{stack_name}-server-sg-docdb'.format(stack_name=self.stack_name)
    )
    sg_docdb_server.add_ingress_rule(peer=sg_use_docdb, connection=aws_ec2.Port.tcp(27017),
      description='docdb-client-sg')
    cdk.Tags.of(sg_docdb_server).add('Name', 'docdb-server-sg')

    docdb_cluster_name = self.node.try_get_context('docdb_cluster_name')
    docdb_cluster_name = docdb_cluster_name if docdb_cluster_name else self.stack_name
    docdb_cluster = aws_docdb.DatabaseCluster(self, 'DocDB',
      db_cluster_name=docdb_cluster_name,
      master_user=aws_docdb.Login(
        username='docdbuser'
      ),
      # instance_type=aws_ec2.InstanceType('r5.xlarge'),
      instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.MEMORY5, aws_ec2.InstanceSize.LARGE),
      instances=3,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_NAT),
      vpc=vpc,
      security_group=sg_docdb_server,
      preferred_maintenance_window='sun:18:00-sun:18:30',
      removal_policy=cdk.RemovalPolicy.RETAIN
    )

    #[Warning at /docdb-sm/Database/RotationSingleUser/SecurityGroup] Ignoring Egress rule since 'allowAllOutbound' is set to true;
    # To add customize rules, set allowAllOutbound=false on the SecurityGroup
    #docdb_cluster.add_rotation_single_user()

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
      security_group_ids=[sg_use_docdb.security_group_id],
      subnet_id=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_NAT).subnet_ids[0]
    )

    cdk.CfnOutput(self, 'StackName', value=self.stack_name, export_name='StackName')
    cdk.CfnOutput(self, 'VpcId', value=vpc.vpc_id, export_name='VpcId')

    cdk.CfnOutput(self, 'DocumentDBClusterName', value=docdb_cluster.cluster_identifier, export_name='DocumentDBClusterName')
    cdk.CfnOutput(self, 'DocumentDBCluster', value=docdb_cluster.cluster_endpoint.socket_address, export_name='DocumentDBCluster')
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_secretsmanager/README.html
    # secret_arn="arn:aws:secretsmanager:<region>:<account-id-number>:secret:<secret-name>-<random-6-characters>",
    cdk.CfnOutput(self, 'DocDBSecret', value=docdb_cluster.secret.secret_name, export_name='DocDBSecret')

    cdk.CfnOutput(self, 'SageMakerRole', value=sagemaker_notebook_role.role_name, export_name='SageMakerRole')
    cdk.CfnOutput(self, 'SageMakerNotebookInstance', value=docdb_workbench.notebook_instance_name, export_name='SageMakerNotebookInstance')
    cdk.CfnOutput(self, 'SageMakerNotebookInstanceLifecycleConfig', value=docdb_workbench.lifecycle_config_name, export_name='SageMakerNotebookInstanceLifecycleConfig')

app = cdk.App()
DocumentdbStack(app, 'AmazonDocDBWithNotebook', env=cdk.Environment(
  account=os.environ['CDK_DEFAULT_ACCOUNT'],
  region=os.environ['CDK_DEFAULT_REGION']))

app.synth()
