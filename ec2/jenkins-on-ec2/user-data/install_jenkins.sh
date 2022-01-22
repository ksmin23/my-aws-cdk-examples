#!/bin/bash -

sudo yum update -y
sudo yum install -y git

sudo wget -O /etc/yum.repos.d/jenkins.repo https://pkg.jenkins.io/redhat-stable/jenkins.repo
sudo rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io.key
sudo yum upgrade

sudo amazon-linux-extras install -y epel

sudo yum install -y java-11-amazon-corretto
sudo yum install -y jenkins

sudo yum install -y nginx

sudo sed -i.bak -e "s/JENKINS_LISTEN_ADDRESS=\"\"/JENKINS_LISTEN_ADDRESS=\"127.0.0.1\"/g" /etc/sysconfig/jenkins

sudo cat <<EOF > /etc/nginx/default.d/jenkins.conf
location / {
  proxy_pass http://localhost:8080;
  proxy_set_header X-Real-IP \$remote_addr;
  proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
  proxy_set_header Host \$http_host;
}
EOF

sudo systemctl daemon-reload

sudo systemctl status jenkins
sudo systemctl start jenkins
sudo systemctl status jenkins

sudo systemctl status nginx
sudo systemctl start nginx
sudo systemctl status nginx

