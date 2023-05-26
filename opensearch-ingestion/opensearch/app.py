#!/usr/bin/env python3
import os

from cdk_stacks import (
  BastionHostEC2InstanceStack,
  OpensearchStack,
  OpsDomainIngestionStack,
  OpsDomainPipelineRoleStack,
  VpcStack,
)

import aws_cdk as cdk


AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

ops_dmain_vpc = VpcStack(app, "OpsDomainVpc",
  env=AWS_ENV)

ops_domain_stack = OpensearchStack(app, "OpsDomainStack",
  ops_dmain_vpc.vpc,
  env=AWS_ENV)
ops_domain_stack.add_dependency(ops_dmain_vpc)

bastion_host = BastionHostEC2InstanceStack(app, "OpsClientEC2Stack",
  ops_dmain_vpc.vpc,
  ops_domain_stack.sg_opensearch_client,
  env=AWS_ENV)
bastion_host.add_dependency(ops_domain_stack)

domain_pipeline_role = OpsDomainPipelineRoleStack(app, 'OpsDomainPipelineRoleStack',
  ops_domain_stack.opensearch_domain_arn,
  env=AWS_ENV)
domain_pipeline_role.add_dependency(ops_domain_stack)

ops_domain_ingestion_stack = OpsDomainIngestionStack(app, "OpsDomainIngestionStack",
  domain_pipeline_role.iam_role.role_arn,
  ops_domain_stack.opensearch_domain_endpoint,
  ops_domain_stack.sg_opensearch_cluster,
  ops_dmain_vpc.vpc,
  env=AWS_ENV)
ops_domain_ingestion_stack.add_dependency(domain_pipeline_role)

app.synth()
