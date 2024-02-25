#!/bin/bash

# Set a right conda or anaconda3 path according to the Deep Learning AMIs
export PATH=/opt/conda/bin:$PATH

wget -q -O /home/ec2-user/webui.sh https://raw.githubusercontent.com/AUTOMATIC1111/stable-diffusion-webui/master/webui.sh

export COMMANDLINE_ARGS="--port 7860 --listen --enable-console-prompts --disable-console-progressbars"
export venv_dir="-"
export NO_TCMALLOC="True"

chown ec2-user /home/ec2-user/webui.sh
chmod +x /home/ec2-user/webui.sh

nohup /home/ec2-user/webui.sh >/home/ec2-user/sd-webui.log 2>&1 &
