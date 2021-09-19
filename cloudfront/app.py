#!/usr/bin/env python3
import os

from aws_cdk import (
  core as cdk,
  aws_cloudfront as cloudfront,
  aws_cloudfront_origins as cf_origins,
  aws_iam,
  aws_s3 as s3
)


class MyStaticSiteStack(cdk.Stack):

  def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # The code that defines your stack goes here
    s3_bucket_name = self.node.try_get_context('s3_bucket_for_static_content')
    site_bucket = s3.Bucket.from_bucket_name(self, "S3BucketForStaticContent", s3_bucket_name)

    cloudfrontOAI = cloudfront.OriginAccessIdentity(self, 'CloudFrontOAI',
      comment="Allows CloudFront to reach the bucket: {name}".format(name=s3_bucket_name)
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
      error_responses=[cloudfront.ErrorResponse(http_status=403, response_http_status=200,
        response_page_path='/index.html', ttl=cdk.Duration.seconds(10))]
    )

    cdk.CfnOutput(self, 'StackName', value=self.stack_name, export_name='StackName')
    cdk.CfnOutput(self, 'SiteBucket', value=site_bucket.bucket_name, export_name='SiteBucket')
    cdk.CfnOutput(self, 'DistributionId', value=distribution.distribution_id, export_name='DistributionId')
    cdk.CfnOutput(self, 'DistributionDomainName', value=distribution.distribution_domain_name, export_name='DistributionDomainName')
    cdk.CfnOutput(self, 'CloudFrontOAI', value=cloudfrontOAI.cloud_front_origin_access_identity_s3_canonical_user_id, export_name='CloudFrontOAI')


app = cdk.App()
MyStaticSiteStack(app, "MyStaticSiteStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
