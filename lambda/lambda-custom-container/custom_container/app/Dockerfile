FROM public.ecr.aws/lambda/python:3.9.2022.12.02.20

# install java
RUN yum install -y java-17-amazon-corretto-devel.x86_64

# Setup JAVA_HOME -- useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-17-amazon-corretto.x86_64
RUN export JAVA_HOME

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY app.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "app.lambda_handler" ]