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

    sagemaker_notebook_role_policy_doc = aws_iam.PolicyDocument()
    sagemaker_notebook_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:s3:::aws-neptune-notebook",
        "arn:aws:s3:::aws-neptune-notebook/*"],
      "actions": ["s3:GetObject",
        "s3:ListBucket"]
    }))

    sagemaker_notebook_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:neptune-db:{region}:{account}:{cluster_id}/*".format(
        region=cdk.Aws.REGION, account=cdk.Aws.ACCOUNT_ID, cluster_id=graph_db.attr_cluster_resource_id)],
      "actions": ["neptune-db:connect"]
    }))

    sagemaker_notebook_role = aws_iam.Role(self, 'SageMakerNotebookForNeptuneWorkbenchRole',
      role_name=f'AWSNeptuneNotebookRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      #XXX: use inline_policies to work around https://github.com/aws/aws-cdk/issues/5221
      inline_policies={
        'AWSNeptuneNotebook': sagemaker_notebook_role_policy_doc
      }
    )

    neptune_wb_lifecycle_content = '''#!/bin/bash
sudo -u ec2-user -i <<'EOF'

echo "export GRAPH_NOTEBOOK_AUTH_MODE=DEFAULT" >> ~/.bashrc
echo "export GRAPH_NOTEBOOK_HOST={NeptuneClusterEndpoint}" >> ~/.bashrc
echo "export GRAPH_NOTEBOOK_PORT={NeptuneClusterPort}" >> ~/.bashrc
echo "export NEPTUNE_LOAD_FROM_S3_ROLE_ARN=''" >> ~/.bashrc
echo "export AWS_REGION={AWS_Region}" >> ~/.bashrc

aws s3 cp s3://aws-neptune-notebook/graph_notebook.tar.gz /tmp/graph_notebook.tar.gz
rm -rf /tmp/graph_notebook
tar -zxvf /tmp/graph_notebook.tar.gz -C /tmp
/tmp/graph_notebook/install.sh
EOF
'''.format(NeptuneClusterEndpoint=graph_db.attr_endpoint,
    NeptuneClusterPort=graph_db.attr_port,
    AWS_Region=cdk.Aws.REGION)

    neptune_wb_lifecycle_config_prop = aws_sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
      content=cdk.Fn.base64(neptune_wb_lifecycle_content)
    )

    neptune_wb_lifecycle_config = aws_sagemaker.CfnNotebookInstanceLifecycleConfig(self, 'NpetuneWorkbenchLifeCycleConfig',
      notebook_instance_lifecycle_config_name='NeptuneWorkbenchLifeCycleConfig',
      on_start=[neptune_wb_lifecycle_config_prop]
    )

    neptune_workbench = aws_sagemaker.CfnNotebookInstance(self, 'NeptuneWorkbench',
      instance_type='ml.t2.medium',
      role_arn=sagemaker_notebook_role.role_arn,
      lifecycle_config_name=neptune_wb_lifecycle_config.notebook_instance_lifecycle_config_name,
      notebook_instance_name='NeptuneWorkbench',
      root_access='Disabled',
      security_group_ids=[sg_graph_db_client.security_group_id],
      subnet_id=graph_db_subnet_group.subnet_ids[0]
    )

    cdk.CfnOutput(self, 'SageMakerNotebookInstanceName',
      value=neptune_workbench.notebook_instance_name,
      export_name=f'{self.stack_name}-NotebookInstanceName')