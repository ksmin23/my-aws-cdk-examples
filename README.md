# AWS CDK Python Examples

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

This repository contains a set of example projects for the [AWS Cloud Development Kit](https://docs.aws.amazon.com/cdk/api/latest/)

| Example | Description | Tags |
|---------|-------------|------|
| [api-gateway/cognito-api-lambda](./api-gateway/cognito-api-lambda/) | ![amazon-cognito-api-lambda](./api-gateway/cognito-api-lambda/amazon-cognito-api-lambda.svg) | api-gateway, cognito, lambda |
| [api-gateway/dynamodb](./api-gateway/dynamodb/) | ![apigw-dynamodb-arch](./api-gateway/dynamodb/apigw-dynamodb-arch.svg) | api-gateway, dynamodb |
| [api-gateway/dynamodb-cognito](./api-gateway/dynamodb-cognito/) | ![apigw-cognito-dynamodb-arch](./api-gateway/dynamodb-cognito/apigw-cognito-dynamodb-arch.svg) | api-gateway, cognito, dynamodb |
| [api-gateway/kds-proxy](./api-gateway/kds-proxy/) | ![apigw-kds-proxy-arch](./api-gateway/kds-proxy/apigw-kds-proxy-arch.svg) | api-gateway, kinesis data streams |
| [api-gateway/kds-proxy-cognito](./api-gateway/kds-proxy-cognito/) | ![apigw-kds-proxy-cognito-arch](./api-gateway/kds-proxy-cognito/apigw-kds-proxy-cognito-arch.svg) | api-gateway, cognito, kinesis data streams |
| [api-gateway/logging-api-calls-to-firehose](./api-gateway/logging-api-calls-to-firehose/) | ![logging-api-calls-to-firehose](./api-gateway/logging-api-calls-to-firehose/logging-api-calls-to-firehose.svg) | api-gateway, kinesis data firehose |
| [api-gateway/logging-api-calls-to-cloudwatch-logs](./api-gateway/logging-api-calls-to-cloudwatch-logs/) | ![logging-api-calls-to-cloudwatch-logs](./api-gateway/logging-api-calls-to-cloudwatch-logs/logging-api-calls-to-cloudwatch-logs.svg) | api-gateway, cloudwatch logs subscription filters with kinesis data firehose |
| [athena](./athena/) | ![athena-arch](./athena/aws-athena-arch.svg) | athena (named query, work group), s3 |
| [batch/batch-with-ec2](./batch/batch-with-ec2/) | Launch AWS Batch | aws batch |
| [cloudfront/static-site](./cloudfront/static-site/) | ![cloudfront-s3-static-site-arch](./cloudfront/static-site/cloudfront-s3-static-site-arch.svg) | cloudfront |
| [dms/aurora_mysql-to-kinesis](./dms/aurora_mysql-to-kinesis/) | ![dms-mysql-to-kinesis-arch](./dms/aurora_mysql-to-kinesis/dms-mysql-to-kinesis-arch.svg) | dms, mysql, kinesis |
| [dms/aurora_mysql-to-s3](./dms/aurora_mysql-to-s3/) | ![dms-mysql-to-s3-arch](./dms/aurora_mysql-to-s3/dms-mysql-to-s3-arch.svg) | dms, mysql, s3 |
| [documentdb](./documentdb/) | ![documentdb-sagemaker-arch](./documentdb/documentdb-sagemaker-arch.svg) | documentdb(docdb), secerts manager, sagemaker|
| [documentdb-elastic-clusters](./documentdb-elastic-clusters/) | ![docdb-elastic-arch](./documentdb-elastic-clusters/docdb-elastic-arch.svg) | documentdb elastic clusters(docdb-elastic), secerts manager|
| [dynamodb](./dynamodb/) | ![dynamodb-arch](./dynamodb/dynamodb-arch.svg) | dynamodb |
| [ec2/vpc](./ec2/vpc/) | ![aws-vpc](./ec2/vpc/aws-vpc.svg) | vpc |
| [ec2/import-existing-vpc](./ec2/import-existing-vpc/) | ![aws-existing-vpc](./ec2/import-existing-vpc/aws-existing-vpc.svg) | vpc |
| [ec2/jenkins-on-ec2](./ec2/jenkins-on-ec2/) | ![jenkins-on-ec2](./ec2/jenkins-on-ec2/jenkins-on-ec2.svg) | jenkins, ec2 |
| [ec2/jupyter-on-dlami](./ec2/jupyter-on-dlami/) | Launch Jupyter Server on Amazon Deep Learning AMI | jupyter, ec2, DLAMI |
| [elasticache/redis](./elasticache/redis/) | ![elasticache-redis-arch](./elasticache/redis/elasticache-for-redis-arch.svg) | redis, redis-cluster |
| [elasticsearch](./elasticsearch/) | ![amazon-es-arch](./elasticsearch/amazon-es-arch.svg) | elasticsearch |
| [opensearch/cfn-domain](./opensearch-service/cfn-domain) | ![amazon-es-arch](./opensearch-service/cfn-domain/amazon-opensearch-arch.svg) | opensearch created with cdk.aws_opensearch.CfnDomain construct |
| [opensearch/domain](./opensearch-service/domain) | ![amazon-es-arch](./opensearch-service/domain/amazon-opensearch-arch.svg) | opensearch created with cdk.aws_opensearch.Domain construct |
| [emr](./emr/) | Launch an Amazon EMR cluster | emr, Hive, Spark, JupyterHub, Hudi, Iceberg  |
| [emr-serverless](./emr-serverless/) | Launch an Amazon EMR Serverless Applation | emr serverless |
| [emr-studio](./emr-studio/) | Launch an Amazon EMR Studio | emr studio |
| [glue/cdc-parquet-to-apache-iceberg](./glue/cdc-parquet-to-apache-iceberg/) | ![glue-job-cdc-parquet-to-iceberg-arch](./glue/cdc-parquet-to-apache-iceberg/glue-job-cdc-parquet-to-iceberg-arch.svg) | aws glue, Apache Iceberg, Parquet |
| [kinesis-data-firehose/data-transform](./kinesis-data-firehose/data-transform/) | ![firehose_data_transform](./kinesis-data-firehose/data-transform/firehose_data_transform.svg) | kinesis firehose, lambda, s3, schema-validation |
| [kinesis-data-firehose/dynamic-partitioning/inline](./kinesis-data-firehose/dynamic-partitioning/inline/) | ![firehose_dynamic_partition_with_inline](./kinesis-data-firehose/dynamic-partitioning/inline/firehose_dynamic_partition_with_inline.svg) | kinesis firehose, s3, dynamic-partitioning, jq |
| [kinesis-data-firehose/dynamic-partitioning/lambda](./kinesis-data-firehose/dynamic-partitioning/lambda/) | ![firehose_dynamic_partition_with_lambda](./kinesis-data-firehose/dynamic-partitioning/lambda/firehose_dynamic_partition_with_lambda.svg) | kinesis firehose, s3, dynamic-partitioning, lambda |
| [kinesis-data-firehose/ekk-stack](./kinesis-data-firehose/ekk-stack/) | ![amazon-ekk-stack-arch](./kinesis-data-firehose/ekk-stack/amazon-ekk-stack-arch.svg) | kinesis firehose, s3, Elasticsearch, bastion host |
| [kinesis-data-firehose/opskk-stack](./kinesis-data-firehose/opskk-stack/) | ![amazon-opskk-stack-arch](./kinesis-data-firehose/opskk-stack/amazon-opskk-stack-arch.svg) | kinesis firehose, s3, OpenSearch, bastion host |
| [kinesis-data-streams/to-kinesis-data-firehose](./kinesis-data-streams/to-kinesis-data-firehose/) | ![amazon-ekk-stack-arch](./kinesis-data-streams/to-kinesis-data-firehose/kinesis_streams_to_firehose_to_s3.svg) | kinesis data streams, kinesis firehose, s3 |
| [lambda/alb-lambda](./lambda/alb-lambda/) | ![aws-alb-lambda](./lambda/alb-lambda/aws-alb-lambda-arch.svg) | lambda, application load balancer |
| [lambda/alb-path-routing-lambda](./lambda/alb-path-routing-lambda/) | ![alb-path-routing-lambda](./lambda/alb-path-routing-lambda/aws-alb-path-routing-lambda-arch.svg) | lambda, application load balancer |
| [lambda/async-invoke](./lambda/async-invoke/) | ![aws-lambda-async-invocation](./lambda/async-invoke/aws-lambda-async-invocation.svg) | lambda, sns, event-bridge |
| [lambda/lambda-custom-container](./lambda/lambda-custom-container/) | ![aws-lambda-custom-container](./lambda/lambda-custom-container/aws-lambda-custom-container.svg) | lambda, ecr, custom container |
| [memorydb-for-redis](./memorydb/) | ![memorydb-for-redis](./memorydb/amazon-memorydb.svg) | memorydb |
| [msk](./msk/) | ![msk-arch](./msk/msk-arch.svg) | msk(kafka) |
| [msk-serverless](./msk-serverless/) | ![msk-serverless-arch](./msk-serverless/msk-serverless-arch.svg) | msk serverless(kafka) |
| [mwaa(airflow)](./mwaa/) | ![mwaa-arch](./mwaa/mwaa-arch.svg) | mwaa(airflow) |
| [neptune](./neptune/) | ![neptune-arch](./neptune/neptune-arch.svg) | sagemaker, neptune |
| [rds/aurora_mysql](./rds/aurora_mysql/) | ![aurora_mysql](./rds/aurora_mysql/aurora_mysql-arch.svg) | aurora mysql, secrets manager |
| [rds/aurora_postgresql](./rds/aurora_postgresql/) | ![aurora_postgresql](./rds/aurora_postgresql/aurora_postgresql-arch.svg) | aurora postgresql, secrets manager |
| [rds/rds_proxy-aurora_mysql](./rds/rds_proxy-aurora_mysql/) | ![rds_proxy-aurora_mysql](./rds/rds_proxy-aurora_mysql/rds_proxy-aurora_mysql-arch.svg) | rds-proxy, aurora mysql, secrets manager |
| [rds/mariadb](./rds/mariadb/) | ![mariadb-arch](./rds/mariadb/mariadb-arch.svg) | mariadb, secrets manager |
| [rds/sagemaker-aurora_mysql](./rds/sagemaker-aurora_mysql/) | ![sagemaker-aurora_mysql](./rds/sagemaker-aurora_mysql/mysql-sagemaker-arch.svg) | rds-proxy, aurora mysql, secrets manager, sagemaker |
| [redshift-serverless](./redshift-serverless/) | ![redshift-serverless-arch](./redshift-serverless/redshift-serverless-arch.svg) | redshift-serverless |
| [redshift-streaming-ingestion/from-kinesis](./redshift-streaming-ingestion/from-kinesis/) | ![redshift_streaming_from_kds](./redshift-streaming-ingestion/from-kinesis/redshift_streaming_from_kds.svg) | redshift streaming ingestion from kinesis |
| [redshift-streaming-ingestion/from-msk](./redshift-streaming-ingestion/from-msk/) | ![redshift_streaming_from_msk](./redshift-streaming-ingestion/from-msk/redshift_streaming_from_msk.svg) | redshift streaming ingestion from msk |
| [redshift-streaming-ingestion/from-msk-serverless](./redshift-streaming-ingestion/from-msk-serverless/) | ![redshift_streaming_from_msk_serverless](./redshift-streaming-ingestion/from-msk-serverless/redshift_streaming_from_msk_serverless.svg) | redshift streaming ingestion from msk serverless |
| [sagemaker/notebook](./sagemaker/notebook/) | Launch an Amazon SageMaker Notebook Instance | sagemaker notebook instance |
| [sagemaker/studio](./sagemaker/studio/) | Launch an Amazon SageMaker Studio | sagemaker studio |

Enjoy!

## Useful commands

 * `npm install -g aws-cdk`          Install the AWS CDK Toolkit (the `cdk` command).
 * `npm install -g aws-cdk@latest`   Install the latest AWS CDK Toolkit (the `cdk`command).
 * `cdk init app --language python`  Create a new, empty CDK Python project.
 * `cdk bootstrap --profile <AWS Profile>` Deploys the CDK Toolkit staging stack; see [Bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html)

## References

 * [Working with the AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/work-with.html)
 * [Your first AWS CDK app](https://docs.aws.amazon.com/cdk/latest/guide/hello_world.html)
 * [AWS CDK v2 Reference Documentation](https://docs.aws.amazon.com/cdk/api/v2/)
 * [AWS CDK Toolkit (cdk command)](https://docs.aws.amazon.com/cdk/v2/guide/cli.html)
 * [AWS CDK Workshop](https://cdkworkshop.com/)
 * [Construct Hub: Open-source CDK libraries](https://constructs.dev/)
 * [aws-samples/aws-cdk-examples](https://github.com/aws-samples/aws-cdk-examples)

