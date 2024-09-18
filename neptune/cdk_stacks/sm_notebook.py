#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam,
  aws_sagemaker
)
from constructs import Construct


class SageMakerNotebookStack(Stack):

  def __init__(self, scope: Construct, id: str, graph_db, sg_graph_db_client, graph_db_subnet_group, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    sagemaker_notebook_policy_doc = aws_iam.PolicyDocument()
    sagemaker_notebook_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "NeptuneAccess",
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:neptune-db:{region}:{account}:{cluster_id}/*".format(
        region=cdk.Aws.REGION, account=cdk.Aws.ACCOUNT_ID, cluster_id=graph_db.attr_cluster_resource_id)],
      "actions": ["neptune-db:connect"]
    }))

    sagemaker_notebook_role = aws_iam.Role(self, 'NeptuneSageMakerNotebookRole',
      role_name=f'NeptuneSageMakerNotebookRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      inline_policies={
        'NeptuneSageMakerNotebookPolicy': sagemaker_notebook_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess'),
      ]
    )

    neptune_load_from_s3_role = graph_db.associated_roles[0]
    neptune_ml_role = graph_db.associated_roles[1]

    neptune_wb_lifecycle_content = '''#!/bin/bash
sudo -u ec2-user -i <<'EOF'
echo "export GRAPH_NOTEBOOK_AUTH_MODE=DEFAULT" >> ~/.bashrc
echo "export GRAPH_NOTEBOOK_HOST={NeptuneClusterEndpoint}" >> ~/.bashrc
echo "export GRAPH_NOTEBOOK_PORT={NeptuneClusterPort}" >> ~/.bashrc
echo "export NEPTUNE_LOAD_FROM_S3_ROLE_ARN={NeptuneLoadFromS3RoleArn}" >> ~/.bashrc
echo "export NEPTUNE_ML_ROLE_ARN={NeptuneMLRoleArn}" >> ~/.bashrc
echo "export AWS_REGION={AWS_Region}" >> ~/.bashrc

aws s3 cp s3://aws-neptune-notebook/graph_notebook.tar.gz /tmp/graph_notebook.tar.gz
rm -rf /tmp/graph_notebook
tar -zxvf /tmp/graph_notebook.tar.gz -C /tmp
/tmp/graph_notebook/install.sh
EOF
'''.format(NeptuneClusterEndpoint=graph_db.attr_endpoint,
    NeptuneClusterPort=graph_db.attr_port,
    NeptuneLoadFromS3RoleArn=neptune_load_from_s3_role.role_arn,
    NeptuneMLRoleArn=neptune_ml_role.role_arn,
    AWS_Region=cdk.Aws.REGION)

    neptune_wb_lifecycle_config_prop = aws_sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
      content=cdk.Fn.base64(neptune_wb_lifecycle_content)
    )

    neptune_wb_lifecycle_config = aws_sagemaker.CfnNotebookInstanceLifecycleConfig(self, 'NpetuneLifeCycleConfig',
      notebook_instance_lifecycle_config_name='NeptuneNotebookInstanceLifecycleConfig',
      on_start=[neptune_wb_lifecycle_config_prop]
    )

    notebook_instance_type = self.node.try_get_context('notebook_instance_type') or "ml.t3.medium"
    notebook_name = self.node.try_get_context('notebook_name') or "NeptuneWorkbench"
    neptune_workbench = aws_sagemaker.CfnNotebookInstance(self, 'NeptuneWorkbench',
      instance_type=notebook_instance_type,
      role_arn=sagemaker_notebook_role.role_arn,
      lifecycle_config_name=neptune_wb_lifecycle_config.notebook_instance_lifecycle_config_name,
      notebook_instance_name=f'aws-neptune-notebook-for-{notebook_name}',
      root_access='Disabled',
      security_group_ids=[sg_graph_db_client.security_group_id],
      subnet_id=graph_db_subnet_group.subnet_ids[0]
    )


    cdk.CfnOutput(self, 'SageMakerNotebookInstanceName',
      value=neptune_workbench.notebook_instance_name,
      export_name=f'{self.stack_name}-NotebookInstanceName')