
# Aurora PostgreSQL Access with SageMaker Notebook Instance (Jupyter)

![postgresql-sagemaker-arch](./postgresql-sagemaker-arch.svg)

This is a sample project for Python development with CDK.

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
$ pip install -r requirements.txt
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ cdk -c db_cluster_name='<i>db-cluster-name</i>' synth
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk -c db_cluster_name='<i>db-cluster-name</i>' deploy
</pre>

Also, you can check all CDK Stacks with `cdk list` command.

```
(.venv) $ cdk list
SMAuroraPgSQLVpcStack
SMAuroraPgSQLStack
SMAuroraPgSQLNotebookStack
```

## Clean Up

Delete the CloudFormation stacks by running the below command.

```
(.venv) $ cdk destroy --all
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

 * [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)
 * [psycopg2-binary](https://pypi.org/project/psycopg2-binary/) - Python-PostgreSQL Database Adapter that is a stand-alone package, not requiring a compiler or external libraries
 * [Supported DB engines for DB instance classes](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html#Concepts.DBInstanceClass.Support)
 * [Extension versions for Amazon Aurora PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/AuroraPostgreSQL.Extensions.html)
 * [Amazon Aurora PostgreSQL now supports pgvector for vector storage and similarity search (2023-07-13)](https://aws.amazon.com/about-aws/whats-new/2023/07/amazon-aurora-postgresql-pgvector-vector-storage-similarity-search/)
 * [Amazon RDS for PostgreSQL now supports pgvector for simplified ML model integration (2023-05-03)](https://aws.amazon.com/about-aws/whats-new/2023/05/amazon-rds-postgresql-pgvector-ml-model-integration/)

