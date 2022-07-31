
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
   0   I     129    Tiffany             IT    Tokyo   49882 1973-10-15 12:32:25
   1   I     204      Oscar             IT  Chicago   93507 2006-03-17 23:21:06
   2   I     252      Julia     Purchasing    Seoul   41204 2007-04-26 12:00:28
   3   I     288       Chad             IT    Tokyo   89084 2002-02-06 13:06:02
   4   I     347      James  Manufacturing      SFO   62261 1988-09-23 20:13:34
   5   I     377     Nathan  Manufacturing       NY   45970 1971-03-03 06:06:03
   6   I     434      Emily          Sales      SFO   20443 1994-03-27 02:22:03
   7   I     558     Edward  Manufacturing    Tokyo   85874 1985-08-18 11:37:01
   8   I     633   Danielle          Sales    Seoul   65974 2020-02-16 20:01:22
   9   I     682       Anne     Purchasing      SFO   36606 2000-07-31 17:35:01
   10  I     695       Gina             IT    Tokyo   93670 2006-02-07 23:05:40
   11  I     695    Richard        Finance    Seoul   37034 1998-12-09 20:18:12
   12  I     924  Frederick          Sales  Chicago   48173 1974-05-01 01:23:15
   13  I     951     Hannah     Purchasing       NY   71689 1993-03-07 04:18:21
   14  I     998  Elizabeth  Manufacturing    Seoul   46318 1971-05-27 14:07:43

   [cdc data]
   Op  emp_no      name     department     city  salary                  m_time
   0  U     377    Nathan       Security   Lisbon   50210 2022-07-11 15:12:31.189
   1  U     347     James            R&D   Sydney   56497 2022-07-11 08:48:31.189
   2  I    8826     Kelly        Finance    Tokyo   52185 2006-06-03 17:46:51.000
   3  U     252     Julia             FC   Sydney   89129 2022-07-11 13:07:31.189
   4  I    8787     Chris             IT  Chicago   30662 1991-08-04 05:10:38.000
   5  D     951    Hannah     Purchasing       NY   71689 2022-07-11 08:48:31.189
   6  I    7339  Jonathan          Sales    Seoul   33806 1972-08-24 22:44:20.000
   7  I    7441  Kristine  Manufacturing    Seoul   87117 1990-08-19 21:13:20.000
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

