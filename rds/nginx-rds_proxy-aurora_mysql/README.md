
# RDS Proxy for Aurora MySQL with NGINX

![](./nginx-rds-proxy-aurora_mysql-arch.svg)

This is a RDS Proxy with NGIX project.

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

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

Before synthesizing the CloudFormation, you should set approperly the cdk context configuration file, `cdk.context.json`.

For example:
<pre>
{
  "db_cluster_name": "<i>db-cluster-name</i>",
  "db_secret_name": "<i>your-db-secret-name</i>"
}
</pre>

Now you can now synthesize the CloudFormation template for this code.

Here is a list of CloudFormation stacks to be deployed.

```
(.venv) $ cdk cdk_user list
NginxRDSProxyVpcStack
AuroraMySQLStack
NginxRDSProxyStack
```

## Creating Aurora MySQL cluster

1. :information_source: Create an AWS Secret for your RDS Admin user like this:
   <pre>
   (.venv) $ aws secretsmanager create-secret \
      --name "<i>your_db_secret_name</i>" \
      --description "<i>(Optional) description of the secret</i>" \
      --secret-string '{"username": "admin", "password": <i>"password_of_at_last_8_characters"</i>}'
   </pre>
   For example,
   <pre>
   (.venv) $ aws secretsmanager create-secret \
      --name "dev/rds/admin" \
      --description "admin user for rds" \
      --secret-string '{"username": "admin", "password": <i>"your admin password"</i>}'
   </pre>

2. Create an Aurora MySQL Cluster
   <pre>
   (.venv) $ cdk deploy NginxRDSProxyVpcStack AuroraMySQLStack
   </pre>

## Making RDS Proxy from NGINX

Provision NGINX on an EC2 Instance
   <pre>
   (.venv) $ cdk deploy NginxRDSProxyStack
   </pre>

## Configure MySQL reverse proxy (stream)

1. Login to the EC2 instance where NGIX is running on
   <pre>
   $ mssh ec2-user@instance_id

   Last login: Fri Jul 14 11:17:02 2023 from 211.109.171.253

          __|  __|_  )
          _|  (     /   Amazon Linux 2 AMI
         ___|\___|___|

   https://aws.amazon.com/amazon-linux-2/
   [ec2-user@ip-172-31-5-161 ~]$ cd /etc/nginx/
   [ec2-user@ip-172-31-5-161 nginx]$ pwd
   /etc/nginx
   [ec2-user@ip-172-31-5-161 nginx]$ ls
   conf.d        fastcgi.conf.default    koi-utf     mime.types.default  scgi_params          uwsgi_params.default
   default.d     fastcgi_params          koi-win     nginx.conf          scgi_params.default  win-utf
   fastcgi.conf  fastcgi_params.default  mime.types  nginx.conf.default  uwsgi_params
   </pre>
2. Add the reverse proxy configurations for MySQL into `/etc/nginx/nginx.conf` like this:
   <pre>
   stream {
       server {
         listen 4306; # Reverse Proxy port to access the primary of Aurora MySQL cluster
        
         # Primary of Aurora MySQL cluster
         proxy_pass mysqldb.cluster-cnrh6fettief.us-east-1.rds.amazonaws.com:3306;
       }

       server {
         listen 5306; # Reverse Proxy port to access the replica of Aurora MySQL cluster

         # Replica of Auroral MySQL cluster
         proxy_pass mysqldb.cluster-ro-cnrh6fettief.us-east-1.rds.amazonaws.com:3306;
       }

       # Add as many server block pairs as you will need for your remote accessed MySQL
   }
   </pre>

   After this edit, your configuration will look something similar to this:
   <pre>
   user nginx;
   worker_processes auto;
   error_log /var/log/nginx/error.log;
   pid /run/nginx.pid;

   include /usr/share/nginx/modules/*.conf;

   events {
       worker_connections 1024;
   }

   http {
       # This is where all http server configs go.
   }

   stream {
       server {
         listen 4306;

         proxy_pass mysqldb.cluster-cnrh6fettief.us-east-1.rds.amazonaws.com:3306;
       }

       server {
         listen 5306;

         proxy_pass mysqldb.cluster-ro-cnrh6fettief.us-east-1.rds.amazonaws.com:3306;
       }
   }
   </pre>
3. Test and Run NGIX
   <pre>
   [ec2-user@ip-172-31-5-161 nginx]$ sudo nginx -t
   nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
   nginx: configuration file /etc/nginx/nginx.conf test is successful
   [ec2-user@ip-172-31-5-161 nginx]$ sudo systemctl start nginx
   </pre>

## Remotely access your Amazon Aurora MySQL Cluster through NGINX RDS Proxy from local machine

#### Access to the primary of Aurora MySQL Cluster

<pre>
~ $ mysql -h<i>public-ip-of-nginx-host</i> -P4306 -uadmin -p
Enter password:
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 1162
Server version: 8.0.23 Source distribution

Copyright (c) 2000, 2023, Oracle and/or its affiliates.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
4 rows in set (0.20 sec)

mysql> CREATE DATABASE testdb;
Query OK, 1 row affected (0.21 sec)

mysql> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
| testdb             |
+--------------------+
5 rows in set (0.20 sec)

mysql>
</pre>


#### Access to the replica of Aurora MySQL Cluster

<pre>
~ $ mysql -h<i>public-ip-of-nginx-host</i> -P5306 -uadmin -p
Enter password:
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 1108
Server version: 8.0.23 Source distribution

Copyright (c) 2000, 2023, Oracle and/or its affiliates.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
5 rows in set (0.21 sec)

mysql> CREATE DATABASE testdb;
ERROR 1836 (HY000): Running in read-only mode
mysql>
</pre>

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

## Troubleshooting

 * error log
   ```
   2023/07/14 21:15:48 [emerg]: unknown directive "stream" in /etc/nginx/nginx.conf:85
   ```
 * solution
   ```
   $ sudo yum install -y nginx-mod-stream.x86_64
   ```

## References

 * [Connect using the EC2 Instance Connect CLI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-methods.html#ec2-instance-connect-connecting-ec2-cli)
   <pre>
   $ sudo pip install ec2instanceconnectcli
   $ mssh ec2-user@<i>i-001234a4bf70dec41EXAMPLE</i> # ec2-instance-id
   </pre>
