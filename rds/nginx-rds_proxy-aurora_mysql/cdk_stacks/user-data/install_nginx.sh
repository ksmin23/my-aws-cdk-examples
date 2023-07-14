#!/bin/bash -

sudo yum update -y
sudo yum upgrade

sudo amazon-linux-extras install -y epel

sudo yum install -y nginx
sudo yum install -y nginx-mod-stream.x86_64

sudo systemctl daemon-reload

sudo systemctl status nginx
sudo systemctl start nginx
sudo systemctl status nginx

