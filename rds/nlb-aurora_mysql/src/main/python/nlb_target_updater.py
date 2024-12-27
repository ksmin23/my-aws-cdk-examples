#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
import boto3
import socket


def lambda_handler(event, context):
  cluster_endpoint = os.environ['CLUSTER_ENDPOINT']
  cluster_endpoint_port = int(os.environ.get('CLUSTER_ENDPOINT_PORT', 3306))
  target_group_arn = os.environ['TARGET_GROUP_ARN']
  region_name = os.environ['AWS_REGION']

  # RDS 엔드포인트의 IP 주소 조회
  ip_address = socket.gethostbyname(cluster_endpoint)

  elbv2 = boto3.client('elbv2', region_name=region_name)

  # 현재 타겟 그룹에 등록된 타겟 조회
  current_targets = elbv2.describe_target_health(TargetGroupArn=target_group_arn)['TargetHealthDescriptions']

  # 새 IP 주소 등록 및 이전 IP 주소 제거
  elbv2.register_targets(
    TargetGroupArn=target_group_arn,
    Targets=[{'Id': ip_address, 'Port': cluster_endpoint_port}]
  )

  for target in current_targets:
    if target['Target']['Id'] != ip_address:
      elbv2.deregister_targets(
        TargetGroupArn=target_group_arn,
        Targets=[{'Id': target['Target']['Id'], 'Port': cluster_endpoint_port}]
      )

  print(f"Updated NLB target to {ip_address}")
