# Hosting OpenAI Whisper Model on Amazon SageMaker Asynchronous Inference Endpoint using SageMaker PyTorch DLC

This is a CDK Python project to host the [OpenAI Whisper](https://openai.com/research/whisper) model
on Amazon SageMaker Asynchronous Inference Endpoint.

[OpenAI Whisper](https://openai.com/research/whisper) is a pre-trained model
for automatic speech recognition (ASR) and speech translation.
Trained on 680 thousand hours of labelled data, Whisper models demonstrate a strong ability
to generalize to many datasets and domains without the need for fine-tuning.
Sagemaker JumpStart is the machine learning (ML) hub of SageMaker that provides access
to foundation models in addition to built-in algorithms and end-to-end solution templates
to help you quickly get started with ML.

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

## Prerequisites

In order to host the model on Amazon SageMaker, the first step is to save the model artifacts.
These artifacts refer to the essential components of a machine learning model needed for various applications,
including deployment and retraining.
They can include model parameters, configuration files, pre-processing components,
as well as metadata, such as version details, authorship, and any notes related to its performance.

1. Install required packages
   ```
   (.venv) $ cat requirements-dev.txt
   accelerate==0.30.1
   datasets==2.16.1
   librosa==0.10.2.post1
   openai-whisper>=20230918
   soundfile==0.12.1
   torch==2.1.0
   torchaudio==2.1.0
   transformers==4.38.0

   (.venv) $ pip install -r requirements-dev.txt
   ```

2. Save model artifacts

   The following instructions work well on either `Ubuntu` or `SageMaker Studio`.

   (1) Create a directory for model artifacts.
   ```
   (.venv) mkdir -p model
   ```

   (2) Run the following python code to download OpenAI Whisper model artifacts from Hugging Face model hub.
   ```python
   from transformers import (
       AutoModelForSpeechSeq2Seq,
       WhisperProcessor,
       WhisperTokenizer,
   )

   # Define a directory where you want to save the model
   save_directory = "./model"

   model_id = "openai/whisper-medium"
   model = AutoModelForSpeechSeq2Seq.from_pretrained(model_id)
   model.save_pretrained(save_directory)

   tokenizer = WhisperTokenizer.from_pretrained(model_id)
   tokenizer.save_pretrained(save_directory)

   processor = WhisperProcessor.from_pretrained(model_id)
   processor.save_pretrained(save_directory)
   ```

   (3) Create `model.tar.gz` with model artifacts including your custom [inference scripts](./src/code/).
   ```
   (.venv) tar cvf model.tar --exclude=".ipynb_checkpoints" -C model/ .
   (.venv) tar rvf model.tar --exclude=".ipynb_checkpoints" -C src/ code
   (.venv) gzip model.tar
   ```

   :information_source: For more information about the directory structure of `model.tar.gz`, see [**Model Directory Structure for Deploying Pre-trained PyTorch Models**](https://sagemaker.readthedocs.io/en/stable/frameworks/pytorch/using_pytorch.html#model-directory-structure)

   (4) Upload `model.tar.gz` file into `s3`
   <pre>
   (.venv) export MODEL_URI="s3://{<i>bucket_name</i>}/{<i>key_prefix</i>}/model.tar.gz"
   (.venv) aws s3 cp model.tar.gz ${MODEL_URI}
   </pre>

   :warning: Replace `bucket_name` and `key_prefi` with yours.

3. Set up `cdk.context.json`

   Then, you should set approperly the cdk context configuration file, `cdk.context.json`.

   For example,
   <pre>
   {
     "model_id": "openai/whisper-medium",
     "model_data_source": {
       "s3_bucket_name": "<i>sagemaker-us-east-1-123456789012</i>",
       "s3_object_key_name": "<i>openai-whisper/model.tar.gz</i>"
     }
   }
   </pre>

## Deploy

At this point you can now synthesize the CloudFormation template for this code.

```
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(aws configure get region)
(.venv) $ cdk synth --all
```

Use `cdk deploy` command to create the stack shown above.

```
(.venv) $ cdk deploy --require-approval never --all
```

## Clean Up

Delete the CloudFormation stack by running the below command.

```
(.venv) $ cdk destroy --force --all
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

 * [(AWS Blog) Whisper models for automatic speech recognition now available in Amazon SageMaker JumpStart (2023-10-10)](https://aws.amazon.com/blogs/machine-learning/whisper-models-for-automatic-speech-recognition-now-available-in-amazon-sagemaker-jumpstart/)
 * [(AWS Blog) Host the Whisper Model on Amazon SageMaker: exploring inference options (2024-01-16)](https://aws.amazon.com/blogs/machine-learning/host-the-whisper-model-on-amazon-sagemaker-exploring-inference-options/)
 * [(Example Jupyter Notebooks) Using PyTorch DLC to Host the Whisper Model for Automatic Speech Recognition Tasks](https://github.com/aws-samples/amazon-sagemaker-host-and-inference-whisper-model/blob/main/pytorch/pytorch.ipynb)
 * 🛠️ [sagemaker-huggingface-inference-toolkit](https://github.com/aws/sagemaker-huggingface-inference-toolkit) - SageMaker Hugging Face Inference Toolkit is an open-source library for serving 🤗 Transformers and Diffusers models on Amazon SageMaker.
 * 🛠️ [sagemaker-inference-toolkit](https://github.com/aws/sagemaker-inference-toolkit) - The SageMaker Inference Toolkit implements a model serving stack and can be easily added to any Docker container, making it [deployable to SageMaker](https://aws.amazon.com/sagemaker/deploy/).
 * [AWS Generative AI CDK Constructs](https://awslabs.github.io/generative-ai-cdk-constructs/)
 * [(AWS Blog) Announcing Generative AI CDK Constructs (2024-01-31)](https://aws.amazon.com/blogs/devops/announcing-generative-ai-cdk-constructs/)
 * [SageMaker Python SDK - Hugging Face](https://sagemaker.readthedocs.io/en/stable/frameworks/huggingface/index.html)
 * [Docker Registry Paths and Example Code for Pre-built SageMaker Docker images](https://docs.aws.amazon.com/sagemaker/latest/dg-ecr-paths/sagemaker-algo-docker-registry-paths.html)
 * [Model Directory Structure for Deploying Pre-trained PyTorch Models](https://sagemaker.readthedocs.io/en/stable/frameworks/pytorch/using_pytorch.html#model-directory-structure)
