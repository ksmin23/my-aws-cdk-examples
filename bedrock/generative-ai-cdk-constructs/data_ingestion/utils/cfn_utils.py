#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import boto3
from typing import List


def get_cfn_outputs(stackname: str, region_name: str) -> List:
    cfn = boto3.client('cloudformation', region_name=region_name)
    outputs = {}
    for output in cfn.describe_stacks(StackName=stackname)['Stacks'][0]['Outputs']:
        outputs[output['OutputKey']] = output['OutputValue']
    return outputs
