#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_cloudfront as cloudfront,
  aws_cloudfront_origins as cf_origins,
  aws_iam,
  aws_s3 as s3
)
from constructs import Construct


class MyStaticSiteStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    s3_bucket_name = cdk.CfnParameter(self, 'S3BucketForStaticContents',
      type='String',
      description='s3 bucket that the site contents are deployed to'
    )

    site_bucket = s3.Bucket.from_bucket_name(self, 'S3BucketForStaticSite', s3_bucket_name.value_as_string)

    cloudfrontOAI = cloudfront.OriginAccessIdentity(self, 'CloudFrontOAI',
      comment="Allows CloudFront to reach the bucket: {name}".format(name=s3_bucket_name.value_as_string)
    );
    cloudfrontOAI.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    #XXX: Add policy document the existing s3 bucket
    #XXX: https://stackoverflow.com/questions/60087302/how-to-add-resource-policy-to-existing-s3-bucket-with-cdk-in-javascript
    site_bucket_policy_statement = aws_iam.PolicyStatement(**{
      'actions': ['s3:GetObject'],
      'resources': [site_bucket.arn_for_objects('*')],
      'principals': [aws_iam.CanonicalUserPrincipal(cloudfrontOAI.cloud_front_origin_access_identity_s3_canonical_user_id)]
    })

    s3.CfnBucketPolicy(self, 'SiteBucketPolicy',
      bucket=site_bucket.bucket_name,
      policy_document=aws_iam.PolicyDocument(statements=[site_bucket_policy_statement])
    )

    distribution = cloudfront.Distribution(self, "myDist",
      default_behavior=cloudfront.BehaviorOptions(
        origin=cf_origins.S3Origin(bucket=site_bucket, origin_access_identity=cloudfrontOAI)
      ),
      error_responses=[
        #XXX: If you have accessed root page of cloudfront url (i.e. https://your-domain.cloudfront.net/),
        #XXX: 403:Forbidden error might occur. In order to prevent this error,
        #XXX: configure 403:Forbidden error response page to be 'index.html'
        cloudfront.ErrorResponse(http_status=403, response_http_status=200,
          response_page_path='/index.html', ttl=cdk.Duration.seconds(10)),
        #XXX: Configure 404:NotFound error response page to be 'error.html'
        cloudfront.ErrorResponse(http_status=404, response_http_status=404,
          response_page_path='/error.html', ttl=cdk.Duration.seconds(10))
      ]
    )

    cdk.CfnOutput(self, 'StackName', value=self.stack_name, export_name='StackName')
    cdk.CfnOutput(self, 'SiteBucket', value=site_bucket.bucket_name, export_name='SiteBucket')
    cdk.CfnOutput(self, 'DistributionId', value=distribution.distribution_id, export_name='DistributionId')
    cdk.CfnOutput(self, 'DistributionDomainName', value=distribution.distribution_domain_name, export_name='DistributionDomainName')
    cdk.CfnOutput(self, 'CloudFrontOriginAccessId', value=cloudfrontOAI.cloud_front_origin_access_identity_s3_canonical_user_id, export_name='CloudFrontOAI')


app = cdk.App()
MyStaticSiteStack(app, "MyStaticSiteStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
