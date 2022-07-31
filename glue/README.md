
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

Before synthesizing the CloudFormation, **you first set up Apache Iceberg connector for AWS Glue to use Apache Iceberg with AWS Glue jobs.** (For more information, see [References](#references) (1), (2), or (3))

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

:warning: **You should create a S3 bucket for a glue job script and upload the glue job script file into the s3 bucket.**

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

1. Set up Apache Iceberg connector for AWS Glue to use Apache Iceberg with AWS Glue jobs.
2. Generate fake parquet files
   <pre>
   (.venv) $ pwd
   ~/my-aws-cdk-examples/glue
   (.venv) $ pip install boto3 Faker fastparquet pyarrow pandas # pip install -r requirements-dev.txt
   (.venv) $ python src/utils/gen_fake_cdc_parquet.py

   [full-load data]
      Op  emp_no       name     department     city  salary              m_time
   0   I     477      Jerry             IT       NY   24202 2015-07-07 21:25:11
   1   I     171        Ann     Purchasing  Chicago   41157 1982-03-10 19:34:45
   2   I     750       Kyle             IT  Chicago   56326 1991-03-29 01:23:28
   3   I     787      Megan             IT    Tokyo   62886 2001-12-06 07:12:56
   4   I     846   Michelle     Purchasing       NY   15840 1970-07-11 02:51:10
   5   I     818     Thomas  Manufacturing    Tokyo   28677 2016-06-27 00:43:40
   6   I     903     Carrie        Finance  Chicago   10549 1977-11-06 22:27:21
   7   I     448    Abigail        Finance       NY   78432 2000-11-23 23:26:43
   8   I     354     Jerome        Finance  Chicago   39528 2010-12-08 14:47:37
   9   I     428       Chad  Manufacturing      SFO   72664 1975-05-17 10:28:56
   10  I     440      Kevin             IT  Chicago   63602 2010-01-15 05:33:16
   11  I     635    Crystal             IT      SFO   67660 1992-03-07 01:49:47
   12  I     462      Jared          Sales    Seoul   47919 1988-08-02 14:17:25
   13  I     848  Nathaniel             IT  Chicago   10051 1997-06-16 09:55:19
   14  I     879      Misty  Manufacturing      SFO   86170 2016-11-14 03:49:05

   [cdc data]
   Op  emp_no         name     department     city  salary                  m_time
   0  D     846     Michelle      Marketing   Mumbai   57059 2022-07-11 05:00:06.596
   1  D     818       Thomas      Marketing   Mumbai   40619 2022-07-11 09:19:06.596
   2  U     750         Kyle       Security   Mumbai   30464 2022-07-11 07:09:06.596
   3  D     848    Nathaniel            R&D   Pargue   56841 2022-07-11 11:24:06.596
   4  I    3026    Katherine          Sales    Seoul   86999 2018-06-25 00:50:01.000
   5  I    3973      Michael  Manufacturing       NY   80381 2008-06-06 16:39:15.000
   6  I    4347        Kylie          Sales    Tokyo   15030 1995-03-26 18:08:11.000
   7  I    5032  Christopher          Sales  Chicago   56024 1980-05-16 13:26:11.000
   (.venv) $ ls \*.parquet
    cdc-load-20220730173650.parquet
    full-load-20220730173650.parquet
   </pre>
3. Copy fake parquet files into S3
   <pre>
   (.venv) $ aws mb <i>s3://aws-glue-input-parquet-atq4q5u</i> --region <i>us-east-1</i>
   (.venv) $ aws cp full-load-20220730173650.parquet <i>s3://aws-glue-input-parquet-atq4q5u/full-load/human_resources/employee_details/full-load-20220730173650.parquet</i>
   (.venv) $ aws cp cdc-load-20220730173650.parquet <i>s3://aws-glue-input-parquet-atq4q5u/cdc-load/human_resources/employee_details/cdc-load-20220730173650.parquet</i>
   (.venv) $ aws mb <i>s3://aws-glue-output-iceberg-atq4q5u</i> --region <i>us-east-1</i>
   </pre>
4. Deply glue job using `cdk deploy`
   <pre>
   (.venv) $ ls src/main/python/etl/
    employee-details-cdc-etl.py
    employee-details-full-etl.py
   (.venv) $ aws mb <i>s3://aws-glue-assets-12345678912-us-east-1</i> --region <i>us-east-1</i>
   (.venv) $ aws cp employee-details-full-etl.py <i>s3://aws-glue-assets-12345678912-us-east-1/scripts/employee-details-full-etl.py</i>
   (.venv) $ aws cp employee-details-cdc-etl.py <i>s3://aws-glue-assets-12345678912-us-east-1/scripts/employee-details-cdc-etl.py</i>
   (.venv) $ cdk deploy --require-approval never
   </pre>
5. Run glue job
   <pre>
   (.venv) $ aws glue start-job-run --job-name <i>employee-details-full-etl</i>
   </pre>
6. Check the output logs of the glue job and results in S3
   <pre>
   (.venv) $ aws s3 ls <i>s3://aws-glue-output-iceberg-atq4q5u/human_resources.db/employee_details_iceberg/</i>
                           PRE data/
                           PRE metadata/
   </pre>


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

