#!/usr/bin/env python3
import os
import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_emr,
  aws_iam,
  aws_s3 as s3,
)
from constructs import Construct

random.seed(31)

class EmrStudioStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    vpc_name = self.node.try_get_context("vpc_name")
    vpc = aws_ec2.Vpc.from_lookup(self, "ExistingVPC",
      is_default=True,
      vpc_name=vpc_name)

    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    # vpc = aws_ec2.Vpc(self, "EmrStudioVPC",
    #   max_azs=2,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )
    EMR_STUDIO_NAME = self.node.try_get_context("emr_studio_name")

    S3_BUCKET_SUFFIX = ''.join(random.sample((string.ascii_lowercase + string.digits), k=7))
    s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: cdk.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name="{studio_name}-emr-studio-{region}-{suffix}".format(
        studio_name=EMR_STUDIO_NAME, region=cdk.Aws.REGION, suffix=S3_BUCKET_SUFFIX))

    sg_emr_studio_workspace = aws_ec2.SecurityGroup(self, 'EmrStudioWorkspaceSG',
      vpc=vpc,
      allow_all_outbound=False,
      description='Workspace security group id associated with the Amazon EMR Studio',
      security_group_name=f'{EMR_STUDIO_NAME}-emr-studio-workspace'
    )
    cdk.Tags.of(sg_emr_studio_workspace).add('Name', 'emr-studio-workspace')

    sg_emr_studio_engine = aws_ec2.SecurityGroup(self, 'EmrStudioEngineSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='Amazon EMR Studio Engine security group',
      security_group_name=f'{EMR_STUDIO_NAME}-emr-studio-engine'
    )
    cdk.Tags.of(sg_emr_studio_engine).add('Name', 'emr-studio-engine')

    sg_emr_studio_engine.add_ingress_rule(peer=sg_emr_studio_workspace, connection=aws_ec2.Port.tcp(18888),
      description='Allow inbound traffic to EngineSecurityGroup ( from notebook to cluster for port 18888 )')

    sg_emr_studio_workspace.add_egress_rule(peer=sg_emr_studio_engine, connection=aws_ec2.Port.tcp(18888),
      description='Allow outbound traffic from WorkspaceSecurityGroup ( from notebook to cluster for port 18888 )')
    sg_emr_studio_workspace.add_egress_rule(peer=aws_ec2.Peer.any_ipv4(), connection=aws_ec2.Port.tcp(443))

    emr_studio_service_role_policy_doc = aws_iam.PolicyDocument()

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowEMRReadOnlyActions",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "elasticmapreduce:ListInstances",
        "elasticmapreduce:DescribeCluster",
        "elasticmapreduce:ListSteps"
      ],
      "resources": ["*"]
    }))

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowEC2ENIActions",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "ec2:CreateNetworkInterfacePermission",
        "ec2:DeleteNetworkInterface"
      ],
      "resources": ["arn:aws:ec2:*:*:network-interface/*"]
    }))

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowEC2ENIAttributeAction",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "ec2:ModifyNetworkInterfaceAttribute"
      ],
      "resources": [
        "arn:aws:ec2:*:*:instance/*",
        "arn:aws:ec2:*:*:network-interface/*",
        "arn:aws:ec2:*:*:security-group/*"
      ]
    }))
   
    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowEC2SecurityGroupActions",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:DeleteNetworkInterfacePermission"
      ],
      "resources": [ "*" ]
    }))

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowDefaultEC2SecurityGroupsCreation",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "ec2:CreateSecurityGroup"
      ],
      "resources": [ "arn:aws:ec2:*:*:security-group/*" ]
    }))

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowDefaultEC2SecurityGroupsCreationInVPC",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "ec2:CreateSecurityGroup"
      ],
      "resources": [ "arn:aws:ec2:*:*:vpc/*" ]
    }))

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowAddingEMRTagsDuringDefaultSecurityGroupCreation",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "ec2:CreateTags"
      ],
      "resources": [ "arn:aws:ec2:*:*:security-group/*" ],
      "conditions": {
        "StringEquals": {
          "ec2:CreateAction": "CreateSecurityGroup"
        }
      }
    }))

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowEC2ENICreation",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "ec2:CreateNetworkInterface"
      ],
      "resources": [ "arn:aws:ec2:*:*:network-interface/*" ]
    }))

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowEC2ENICreationInSubnetAndSecurityGroup",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "ec2:CreateNetworkInterface"
      ],
      "resources": [
        "arn:aws:ec2:*:*:subnet/*",
        "arn:aws:ec2:*:*:security-group/*"
      ]
    }))

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowAddingTagsDuringEC2ENICreation",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "ec2:CreateTags"
      ],
      "resources": [ "arn:aws:ec2:*:*:network-interface/*" ],
      "conditions": {
        "StringEquals": {
          "ec2:CreateAction": "CreateNetworkInterface"
        }
      }
    }))

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowEC2ReadOnlyActions",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeTags",
        "ec2:DescribeInstances",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs"
      ],
      "resources": [ "*" ]
    }))

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowSecretsManagerReadOnlyActions",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "secretsmanager:GetSecretValue"
      ],
      "resources": [ "arn:aws:secretsmanager:*:*:secret:*" ]
    }))

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "AllowS3NotebookStorage",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "s3:Put*",
        "s3:Get*",
        "s3:GetEncryptionConfiguration",
        "s3:List*",
        "s3:Delete*"
      ],
      "resources": [ "*" ]
    }))

    emr_studio_service_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "KmsPermission",
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      "resources": [ "*" ]
    }))

    emr_studio_service_role = aws_iam.Role(self, 'EmrStudioServiceRole',
      role_name=f'{EMR_STUDIO_NAME}_EMRStudio_Service_Role',
      assumed_by=aws_iam.ServicePrincipal('elasticmapreduce.amazonaws.com'), 
      inline_policies={
        f'{EMR_STUDIO_NAME}_EMRStudioServiceRolePolicy': emr_studio_service_role_policy_doc
      }
    )

    # http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-emr-studio.html
    emr_cfn_studio = aws_emr.CfnStudio(self, "MyCfnEmrStudio",
        auth_mode="IAM", # [IAM, SSO]
        default_s3_location=f"s3://{s3_bucket.bucket_name}",
        engine_security_group_id=sg_emr_studio_engine.security_group_id,
        name=EMR_STUDIO_NAME,
        service_role=emr_studio_service_role.role_arn,
        subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
        vpc_id=vpc.vpc_id,
        workspace_security_group_id=sg_emr_studio_workspace.security_group_id
    )

    cdk.CfnOutput(self, 'EmrStudioName', value=emr_cfn_studio.name)
    cdk.CfnOutput(self, 'EmrStudioUrl', value=emr_cfn_studio.attr_url)
    cdk.CfnOutput(self, 'EmrStudioId', value=emr_cfn_studio.attr_studio_id)
    cdk.CfnOutput(self, 'EmrStudioDefaultS3Location', value=emr_cfn_studio.default_s3_location)


app = cdk.App()
EmrStudioStack(app, "EmrStudioStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
