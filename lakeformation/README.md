
# AWS Lake Formation CDK Python project to grant permissions on Data Catalog Resources

This is an AWS Lake Formation project for CDK development with Python.

This project shows how to grant AWS Lake Formation permissions on Data Catalog Resources.

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

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ cdk synth -c database_name=<i>lf_testdb</i>
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy -c database_name=<i>lf_testdb</i> --require-approval never
</pre>
> :information_source: Replace `lf_testdb` to your own database name in Glue Data Catalog.

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

After all CDK stacks are successfully deployed, you can see a list of permissions on `lf_testdb` to `GlueJobRoleExample` IAM Role.
<pre>
aws lakeformation list-permissions | jq -r '.PrincipalResourcePermissions[] | select(.Principal.DataLakePrincipalIdentifier | endswith("GlueJobRoleExample"))'
</pre>
> :information_source: `GlueJobRoleExample` is an IAM Role created by this project.

## Clean Up

Delete the CloudFormation stack by running the below command.

<pre>
(.venv) $ cdk destroy --all
</pre>


## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!


## Useful AWS Lake Formation commands

 * `aws lakeformation list-permissions`     Returns a list of the principal permissions on the resource, filtered by the permissions of the caller. See [more](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/lakeformation/list-permissions.html)
 * `aws lakeformation grant-permissions`    Grants permissions to the principal to access metadata in the Data Catalog and data organized in underlying data storage such as Amazon S3. See [more](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/lakeformation/grant-permissions.html)
 * `aws lakeformation revoke-permissions`   Revokes permissions to the principal to access metadata in the Data Catalog and data organized in underlying data storage such as Amazon S3. See [more](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/lakeformation/revoke-permissions.html)
 * `aws lakeformation list-resources`       Lists the resources registered to be managed by the Data Catalog. See [more](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/lakeformation/list-resources.html)


## References

 * [AWS Lake Formation Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/78572df7-d2ee-4f78-b698-7cafdb55135d/en-US)
 * [AWS Lake Formation - Create a data lake administrator](https://docs.aws.amazon.com/lake-formation/latest/dg/getting-started-setup.html#create-data-lake-admin)
 * [AWS Lake Formation - Granting Data Catalog permissions using the named resource method](https://docs.aws.amazon.com/lake-formation/latest/dg/granting-cat-perms-named-resource.html)
 * [AWS Lake Formation Permissions Reference](https://docs.aws.amazon.com/lake-formation/latest/dg/lf-permissions-reference.html)
 * [Troubleshooting Lake Formation](https://docs.aws.amazon.com/lake-formation/latest/dg/troubleshooting.html)
 * [Known issues for AWS Lake Formation](https://docs.aws.amazon.com/lake-formation/latest/dg/limitations.html)
 * [AWS Lake Formation - Working with other AWS services](https://docs.aws.amazon.com/lake-formation/latest/dg/working-with-services.html)
