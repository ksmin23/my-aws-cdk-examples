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

  def __init__(self, scope: Construct, id: str, neptune_graph, neptune_graph_port, sg_neptune_graph_client, neptune_graph_subnet_ids, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    sagemaker_notebook_policy_doc = aws_iam.PolicyDocument()
    sagemaker_notebook_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [
        "arn:aws:s3:::*"
      ],
      "actions": [
        "s3:GetObject",
        "s3:ListBucket"
      ]
    }))

    sagemaker_notebook_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [
        f"arn:aws:logs:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:log-group:/aws/sagemaker/*"
      ],
      "actions": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
    }))

    sagemaker_notebook_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [
        f"arn:aws:neptune-graph:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:*/*"
      ],
      "actions": [
        "neptune-graph:*"
      ]
    }))

    sagemaker_notebook_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [
        f"arn:aws:neptune-graph:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:notebook-instance/*"
      ],
      "actions": [
        "sagemaker:DescribeNotebookInstance"
      ]
    }))

    sagemaker_notebook_role = aws_iam.Role(self, 'SageMakerNotebookNeptuneAnalyticsRole',
      role_name=f'SageMakerNotebookRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      inline_policies={
        'SagemakerNotebookNeptuneAnalyticsPolicy': sagemaker_notebook_policy_doc
      }
    )

    neptune_wb_lifecycle_content = '''#!/bin/bash
sudo -u ec2-user -i <<'EOF'
echo "export GRAPH_NOTEBOOK_AUTH_MODE=IAM" >> ~/.bashrc
echo "export GRAPH_NOTEBOOK_SSL=True" >> ~/.bashrc
echo "export GRAPH_NOTEBOOK_SERVICE=neptune-graph" >> ~/.bashrc
echo "export GRAPH_NOTEBOOK_HOST={NeptuneAnalyticsEndpoint}" >> ~/.bashrc
echo "export GRAPH_NOTEBOOK_PORT={NeptuneAnalyticsPort}" >> ~/.bashrc
echo "export NEPTUNE_LOAD_FROM_S3_ROLE_ARN=''" >> ~/.bashrc
echo "export AWS_REGION={AWS_Region}" >> ~/.bashrc
aws s3 cp s3://aws-neptune-notebook/graph_notebook.tar.gz /tmp/graph_notebook.tar.gz
rm -rf /tmp/graph_notebook
tar -zxvf /tmp/graph_notebook.tar.gz -C /tmp
/tmp/graph_notebook/install.sh
EOF
'''.format(NeptuneAnalyticsEndpoint=neptune_graph.attr_endpoint,
    NeptuneAnalyticsPort=neptune_graph_port,
    AWS_Region=cdk.Aws.REGION)

    neptune_wb_lifecycle_config_prop = aws_sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
      content=cdk.Fn.base64(neptune_wb_lifecycle_content)
    )

    neptune_wb_lifecycle_config = aws_sagemaker.CfnNotebookInstanceLifecycleConfig(self, 'NpetuneWorkbenchLifeCycleConfig',
      notebook_instance_lifecycle_config_name='NeptuneAnalyticsNotebookInstanceLifecycleConfig',
      on_start=[neptune_wb_lifecycle_config_prop]
    )

    notebook_instance_type = self.node.try_get_context('notebook_instance_type') or "ml.t3.medium"
    notebook_name = self.node.try_get_context('notebook_name') or "NeptuneGraphWorkbench"
    neptune_workbench = aws_sagemaker.CfnNotebookInstance(self, 'NeptuneWorkbench',
      instance_type=notebook_instance_type,
      role_arn=sagemaker_notebook_role.role_arn,
      lifecycle_config_name=neptune_wb_lifecycle_config.notebook_instance_lifecycle_config_name,
      notebook_instance_name=f'aws-neptune-analytics-{notebook_name}',
      #XX: set platform_identifier to 'notebook-al2-v2' for Neptune-specific synchronization from a snapshot to a new instance
      # for more information, see https://docs.aws.amazon.com/neptune/latest/userguide/graph-notebooks.html
      platform_identifier='notebook-al2-v2',
      root_access='Disabled',
      security_group_ids=[sg_neptune_graph_client.security_group_id],
      subnet_id=neptune_graph_subnet_ids[0]
    )


    cdk.CfnOutput(self, 'SageMakerNotebookInstanceName',
      value=neptune_workbench.notebook_instance_name,
      export_name=f'{self.stack_name}-NotebookInstanceName')