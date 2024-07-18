# Hosting OpenAI Whisper Model on Amazon SageMaker Real-time Inference Endpoint using SageMaker JumpStart

This is a CDK Python project to host the [OpenAI Whisper](https://openai.com/research/whisper) model
on Amazon SageMaker Real-time Inference Endpoint.

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

## Set up `cdk.context.json`

Then, you should set approperly the cdk context configuration file, `cdk.context.json`.

For example,
<pre>
{
  "jumpstart_model_info": {
    "model_id": "huggingface-asr-whisper-medium",
    "version": "3.0.0"
  }
}
</pre>

:information_source: The `model_id`, and `version` provided by SageMaker JumpStart can be found in [**SageMaker Built-in Algorithms with pre-trained Model Table**](https://sagemaker.readthedocs.io/en/stable/doc_utils/pretrainedmodels.html).

## Deploy

At this point you can now synthesize the CloudFormation template for this code.

```
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
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
 * [(Example Jupyter Notebooks) Using Huggingface DLC to Host the Whisper Model for Automatic Speech Recognition Tasks](https://github.com/aws-samples/amazon-sagemaker-host-and-inference-whisper-model/blob/main/huggingface/huggingface.ipynb)
 * 🛠️ [sagemaker-huggingface-inference-toolkit](https://github.com/aws/sagemaker-huggingface-inference-toolkit) - SageMaker Hugging Face Inference Toolkit is an open-source library for serving 🤗 Transformers and Diffusers models on Amazon SageMaker.
 * 🛠️ [sagemaker-inference-toolkit](https://github.com/aws/sagemaker-inference-toolkit) - The SageMaker Inference Toolkit implements a model serving stack and can be easily added to any Docker container, making it [deployable to SageMaker](https://aws.amazon.com/sagemaker/deploy/).
 * [AWS Generative AI CDK Constructs](https://awslabs.github.io/generative-ai-cdk-constructs/)
 * [(AWS Blog) Announcing Generative AI CDK Constructs (2024-01-31)](https://aws.amazon.com/blogs/devops/announcing-generative-ai-cdk-constructs/)
 * [SageMaker Built-in Algorithms with pre-trained Model Table](https://sagemaker.readthedocs.io/en/stable/doc_utils/pretrainedmodels.html)
