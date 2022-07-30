
# AWS Glue Job CDK Python project!

![glue-job-cdc-parquet-to-iceberg-arch](./glue-job-cdc-parquet-to-iceberg-arch.svg)

This is a glue job project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
(.venv) $ pip install -r requirements.txt
```

Before synthesizing the CloudFormation, you first set up Apache Iceberg connector for AWS Glue to use Apache Iceberg with AWS Glue jobs. (For more information, see [References](#references) (1), (2), or (3))

Then you should set approperly the cdk context configuration.
For example:
<pre>
{
  "vpc_name": "default",
  "glue_assets_s3_bucket_name": "aws-glue-assets-12345678912-us-east-1",
  "glue_job_script_file_name": "employee-details-full-etl.py",
  "glue_job_input_arguments": {
    "--raw_s3_path": "s3://aws-glue-input-parquet-atq4q5u/full-load",
    "--iceberg_s3_path": "s3://aws-glue-output-iceberg-atq4q5u",
    "--catalog": "glue_catalog",
    "--database": "human_resources",
    "--partition_key": "department",
    "--primary_key": "emp_no",
    "--table_name": "employee_details"
  },
  "glue_connections_name": "iceberg-connection",
}
</pre>

:warning: You should create a S3 bucket for a glue job script and upload the glue job script file into the s3 bucket. 

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
(.venv) $ cdk synth 
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy --require-approval never
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Test

1. Generate fake parquet files
   <pre>
   (.venv) $ pwd
   ~/my-aws-cdk-examples/glue
   (.venv) $ pip install boto3 Faker fastparquet pyarrow pandas # pip install -r requirements-dev.txt
   (.venv) $ python src/utils/gen_fake_cdc_parquet.py

    [full-load data]
      Op  emp_no         name     department     city  salary              m_time
    0   I     735        Oscar        Finance    Tokyo   53598 2022-02-10 05:48:13
    1   I     173      Patrick  Manufacturing    Seoul   91282 1999-12-29 07:20:17
    2   I     531        Donna          Sales       NY   68958 2013-11-09 04:44:35
    3   I     967    Elizabeth             IT    Tokyo   66129 1976-05-22 13:44:48
    4   I     332      Richard             IT    Tokyo   11466 1998-01-29 03:53:31
    5   I     603       Daniel  Manufacturing  Chicago   88550 1989-03-14 05:23:51
    6   I     298        James             IT       NY   48561 1987-09-09 03:56:03
    7   I     885       Pamela     Purchasing       NY   41585 1992-12-08 23:30:18
    8   I     631     Kristine             IT  Chicago   98029 1970-11-23 15:01:18
    9   I     933        Brady          Sales    Tokyo   11407 1986-01-16 20:40:20
    10  I     696  Christopher     Purchasing    Tokyo   23312 1995-03-02 09:12:12
    11  I     373      Michael  Manufacturing    Seoul   47757 1977-12-22 09:25:07
    12  I     238        Kelly             IT       NY   56717 2022-06-29 01:32:09
    13  I     729        Larry  Manufacturing    Seoul   56261 2000-04-15 05:03:50
    14  I     699      Jessica     Purchasing      SFO   17897 1982-09-11 22:19:59

    [cdc data]
      Op  emp_no      name department     city  salary                  m_time
    0  D     332   Richard   Security  Seattle   48185 2022-07-10 23:56:31.747
    1  U     332   Richard  Marketing   Lisbon   81701 2022-07-10 21:46:31.747
    2  U     531     Donna   Security   Sydney   59382 2022-07-10 19:37:31.747
    3  U     603    Daniel  Marketing   Lisbon   81001 2022-07-10 21:46:31.747
    0  I    4710  Jeremiah    Finance    Seoul   74361 2003-03-12 03:31:01.000
    1  I    3830     Blake    Finance      SFO   22643 1988-12-25 00:01:42.000
    2  I    9790   Christy         IT    Seoul   49510 2000-02-28 23:40:07.000
    3  I    1021     Kelli      Sales  Chicago   87888 1981-07-14 09:27:52.000
   (.venv) $ ls *.parquet
    cdc-load-20220730173650.parquet
    full-load-20220730173650.parquet
   </pre>
2. Copy fake parquet files into S3
   <pre>
   (.venv) $ aws mb s3://aws-glue-input-parquet-atq4q5u --region us-east-1
   (.venv) $ aws cp full-load-20220730173650.parquet s3://aws-glue-input-parquet-atq4q5u/full-load/human_resources/employee_details/full-load-20220730173650.parquet
   (.venv) $ aws cp cdc-load-20220730173650.parquet s3://aws-glue-input-parquet-atq4q5u/cdc-load/human_resources/employee_details/cdc-load-20220730173650.parquet
   (.venv) $ aws mb s3://aws-glue-output-iceberg-atq4q5u --region us-east-1
   </pre>
3. Deply glue job using `cdk deploy`
   <pre>
   (.venv) $ ls src/main/python/etl/
    employee-details-cdc-etl.py
    employee-details-full-etl.py
   (.venv) $ aws mb s3://aws-glue-assets-12345678912-us-east-1 --region us-east-1
   (.venv) $ aws cp employee-details-full-etl.py s3://aws-glue-assets-12345678912-us-east-1/scripts/employee-details-full-etl.py
   (.venv) $ aws cp employee-details-cdc-etl.py s3://aws-glue-assets-12345678912-us-east-1/scripts/employee-details-cdc-etl.py
   (.venv) $ cdk deploy --require-approval never
   </pre>
4. Run glue job
   <pre>
   (.venv) $ aws glue start-job-run --job-name <i>employee-details-full-etl</i>
   </pre>
5. Check the output logs of the glue job and results in S3

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

- (1) [Apache Iceberg Connector for AWS Glue를 이용하여 데이터레이크 CRUD 하기 \(2022-07-08\)](https://aws.amazon.com/ko/blogs/tech/transactional-datalake-using-apache-iceberg-connector-for-aws-glue/)
- (2) [Use the AWS Glue connector to read and write Apache Iceberg tables with ACID transactions and perform time travel \(2022-06-21\)](https://aws.amazon.com/ko/blogs/big-data/use-the-aws-glue-connector-to-read-and-write-apache-iceberg-tables-with-acid-transactions-and-perform-time-travel/)
- (3) [Implement a CDC-based UPSERT in a data lake using Apache Iceberg and AWS Glue \(2022-06-15\)](https://aws.amazon.com/ko/blogs/big-data/implement-a-cdc-based-upsert-in-a-data-lake-using-apache-iceberg-and-aws-glue/)
- (4) [Apache Iceberg Connector for AWS Glue](https://aws.amazon.com/marketplace/pp/prodview-iicxofvpqvsio)
- (5) [Introduction to AWS Glue and Glue Databrew](https://catalog.us-east-1.prod.workshops.aws/workshops/aaaabcab-5e1e-4bff-b604-781a804763e1/en-US)
- (6) [AWS Glue Immersion day](https://catalog.us-east-1.prod.workshops.aws/workshops/ee59d21b-4cb8-4b3d-a629-24537cf37bb5/en-US)
- (7) [Amazon Athena Workshop - ACID Transactions with Iceberg](https://catalog.us-east-1.prod.workshops.aws/workshops/9981f1a1-abdc-49b5-8387-cb01d238bb78/en-US/90-athena-acid)

