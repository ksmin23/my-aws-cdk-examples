########################################################################################################################
#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.                                                  #
#  SPDX-License-Identifier: Apache License 2.0                                                                         #
#                                                                                                                      #
#  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance      #
#  with the License. You may obtain a copy of the License at                                                           #
#                                                                                                                      #
#   http://www.apache.org/licenses/LICENSE-2.0                                                                         #
#                                                                                                                      #
#  Unless required by applicable law or agreed to in writing, software distributed under the License is distributed    #
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for   #
#  the specific language governing permissions and limitations under the License.                                      #
########################################################################################################################

import json
import boto3
import base64
import urllib3
import os
from botocore.exceptions import ClientError

def get_secret():

  secret_name = os.environ['JenkinsAPIUserTokenSecret']
  region_name = os.environ['AWS_REGION']

  # Create a Secrets Manager client
  session = boto3.session.Session()
  client = session.client(
    service_name='secretsmanager',
    region_name=region_name
  )

  # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
  # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
  # We rethrow the exception by default.

  try:
    get_secret_value_response = client.get_secret_value(
      SecretId=secret_name
    )

  except ClientError as e:
    if e.response['Error']['Code'] == 'DecryptionFailureException':
      # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
      # Deal with the exception here, and/or rethrow at your discretion.
      raise e
    elif e.response['Error']['Code'] == 'InternalServiceErrorException':
      # An error occurred on the server side.
      # Deal with the exception here, and/or rethrow at your discretion.
      raise e
    elif e.response['Error']['Code'] == 'InvalidParameterException':
      # You provided an invalid value for a parameter.
      # Deal with the exception here, and/or rethrow at your discretion.
      raise e
    elif e.response['Error']['Code'] == 'InvalidRequestException':
      # You provided a parameter value that is not valid for the current state of the resource.
      # Deal with the exception here, and/or rethrow at your discretion.
      raise e
    elif e.response['Error']['Code'] == 'ResourceNotFoundException':
      # We can't find the resource that you asked for.
      # Deal with the exception here, and/or rethrow at your discretion.
      raise e
  else:
    # Decrypts secret using the associated KMS CMK.
    # Depending on whether the secret is a string or binary, one of these fields will be populated.
    if 'SecretString' in get_secret_value_response:
      return get_secret_value_response['SecretString']
    else:
      return base64.b64decode(get_secret_value_response['SecretBinary'])
      
def get_secret_value(secert_string):
  # secert json is of format {'key' : 'value'}
  secert_json = json.loads(secert_string)
  # Get values
  return list(secert_json.values())[0]


def lambda_handler(event, context):
  http = urllib3.PoolManager()
  user_api_token = json.loads(get_secret())
  url = get_jenkins_job_url(event)
  user = list(user_api_token.keys())[0]
  api_token = user_api_token[user]
  print('Jenkins remote trigger url: ' + url)
  headers = urllib3.make_headers(basic_auth = user + ':' + api_token)
  r = http.request('GET', url, headers=headers)
  print(r.data)
  if r.status > 299:
    raise Exception('Remote trigger of jenkins failed with status ' + str(r.status))
  return {
    'statusCode': r.status,
    'body': r.data
  }


def get_jenkins_job_url(event):
  jenkins_url = os.environ['JenkinsUrl']
  jenkins_model_deploy_pipeline_name =  'sagemaker-' + event['detail']['ModelPackageGroupName'] + '-modeldeploy'
  jenkins_job_url = jenkins_url + '/job/' + jenkins_model_deploy_pipeline_name + '/'

  job_token = 'token=token'
  cause = 'cause=Model+Package+version+' + event['detail']['ModelPackageArn'] + '+apporval+status+changed+to+' + event['detail']['ModelApprovalStatus']

  jenkins_remote_url_params = job_token + '&' + cause

  return jenkins_job_url + 'buildWithParameters?' + jenkins_remote_url_params
