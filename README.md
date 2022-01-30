# AWS CDK Python Examples

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

This repository contains a set of example projects for the [AWS Cloud Development Kit](https://docs.aws.amazon.com/cdk/api/latest/)

| Example | Description | Tags |
|---------|-------------|------|
| [api-gateway/cognito-api-lambda](./api-gateway/cognito-api-lambda/) | ![amazon-cognito-api-lambda](./api-gateway/cognito-api-lambda/amazon-cognito-api-lambda.svg) | api-gateway, cognito, lambda |
| [api-gateway/dynamodb](./api-gateway/dynamodb/) | ![apigw-dynamodb-arch](./api-gateway/dynamodb/apigw-dynamodb-arch.svg) | api-gateway, dynamodb |
| [api-gateway/dynamodb-cognito](./api-gateway/dynamodb-cognito/) | ![apigw-cognito-dynamodb-arch](./api-gateway/dynamodb-cognito/apigw-cognito-dynamodb-arch.svg) | api-gateway, cognito, dynamodb |
| [cloudfront/static-site](./cloudfront/static-site/) | ![cloudfront-s3-static-site-arch](./cloudfront/static-site/cloudfront-s3-static-site-arch.svg) | cloudfront |
| [documentdb](./documentdb/) | ![documentdb-sagemaker-arch](./documentdb/documentdb-sagemaker-arch.svg) | secerts manager, sagemaker, documentdb |
| [dynamodb](./dynamodb/) | ![dynamodb-arch](./dynamodb/dynamodb-arch.svg) | dynamodb |
| [ec2/vpc](./ec2/vpc/) | ![aws-vpc](./ec2/vpc/aws-vpc.svg) | vpc |
| [ec2/import-existing-vpc](./ec2/import-existing-vpc/) | ![aws-existing-vpc](./ec2/import-existing-vpc/aws-existing-vpc.svg) | vpc |
| [elasticache/redis](./elasticache/redis/) | ![elasticache-redis-arch](./elasticache/redis/elasticache-for-redis-arch.svg) | redis, redis-cluster |
| [elasticsearch](./elasticsearch/) | ![amazon-es-arch](./elasticsearch/amazon-es-arch.svg) | elasticsearch |
| [opensearch](./opensearch-service/) | ![amazon-es-arch](./opensearch-service/amazon-opensearch-arch.svg) | opensearch |
| [kinesis-data-firehose/data-transform](./kinesis-data-firehose/data-transform/) | ![firehose_data_transform](./kinesis-data-firehose/data-transform/firehose_data_transform.svg) | kinesis firehose, lambda, s3, schema-validation |
| [kinesis-data-firehose/dynamic-partitioning/inline](./kinesis-data-firehose/dynamic-partitioning/inline/) | ![firehose_dynamic_partition_with_inline](./kinesis-data-firehose/dynamic-partitioning/inline/firehose_dynamic_partition_with_inline.svg) | kinesis firehose, lambda, s3, dynamic-partitioning |
| [kinesis-data-firehose/dynamic-partitioning/lambda](./kinesis-data-firehose/dynamic-partitioning/lambda/) | ![firehose_dynamic_partition_with_lambda](./kinesis-data-firehose/dynamic-partitioning/lambda/firehose_dynamic_partition_with_lambda.svg) | kinesis firehose, s3, dynamic-partitioning, jq |
| [kinesis-data-firehose/ekk-stack](./kinesis-data-firehose/ekk-stack/) | ![amazon-ekk-stack-arch](./kinesis-data-firehose/ekk-stack/amazon-ekk-stack-arch.svg) | kinesis firehose, s3, elasticsearch, bastion host |
| [lambda/async-invoke](./lambda/async-invoke/) | ![aws-lambda-async-invocation](./lambda/async-invoke/aws-lambda-async-invocation.svg) | lambda, sns, event-bridge |
| [memorydb-for-redis](./memorydb/) | ![memorydb-for-redis](./memorydb/amazon-memorydb.svg) | memorydb |
| [msk](./msk/) | ![msk-arch](./msk/msk-arch.svg) | msk(kafka) |
| [mwaa(airflow)](./mwaa/) | ![mwaa-arch](./mwaa/mwaa-arch.svg) | mwaa(airflow) |
| [neptune](./neptune/) | ![neptune-arch](./neptune/neptune-arch.svg) | sagemaker, neptune |
| [rds/rds_proxy-aurora_mysql](./rds/rds_proxy-aurora_mysql/) | ![rds_proxy-aurora_mysql](./rds/rds_proxy-aurora_mysql/rds_proxy-aurora_mysql-arch.svg) | rds-proxy, aurora mysql, secrets manager |
| [rds/sagemaker-aurora_mysql](./rds/sagemaker-aurora_mysql/) | ![sagemaker-aurora_mysql](./rds/sagemaker-aurora_mysql/mysql-sagemaker-arch.svg) | rds-proxy, aurora mysql, secrets manager, sagemaker |

Enjoy!

## Useful commands

 * `npm install -g aws-cdk`          Install the AWS CDK Toolkit (the `cdk` command).
 * `npm install -g aws-cdk@latest`   Install the latest AWS CDK Toolkit (the `cdk`command).
 * `cdk init app --language python`  Create a new, empty CDK Python project.
 * `cdk bootstrap --profile <AWS Profile>` Deploys the CDK Toolkit staging stack; see [Bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html)

## References

 * [Working with the AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/work-with.html)
 * [Your first AWS CDK app](https://docs.aws.amazon.com/cdk/latest/guide/hello_world.html)
 * [AWS CDK v1 Reference Documentation](https://docs.aws.amazon.com/cdk/api/v1/)
 * [AWS CDK v2 Reference Documentation](https://docs.aws.amazon.com/cdk/api/v2/)
 * [Migrating to AWS CDK v2](https://docs.aws.amazon.com/cdk/v2/guide/migrating-v2.html)
 * [AWS CDK Toolkit (cdk command)](https://docs.aws.amazon.com/cdk/v2/guide/cli.html)
 * [aws-samples/aws-cdk-examples](https://github.com/aws-samples/aws-cdk-examples)

