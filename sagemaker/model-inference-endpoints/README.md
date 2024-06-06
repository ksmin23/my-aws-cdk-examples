# Hosting OpenAI Whisper Model on Amazon SageMaker

This repository contains a set of example CDK Python projects to host the [OpenAI Whisper](https://openai.com/research/whisper) model
on Amazon SageMaker Endpoint.

[OpenAI Whisper](https://openai.com/research/whisper) is a pre-trained model
for automatic speech recognition (ASR) and speech translation.
Trained on 680 thousand hours of labelled data, Whisper models demonstrate a strong ability
to generalize to many datasets and domains without the need for fine-tuning.
Sagemaker JumpStart is the machine learning (ML) hub of SageMaker that provides access
to foundation models in addition to built-in algorithms and end-to-end solution templates
to help you quickly get started with ML.

| Inference Type | Deep Learning Container (DLC) | Description | Example Notebook |
|----------------|-------------------------------|-------------|------------------|
| Asynchronous Inference | [SageMaker JumpStart](./sagemaker-async-inference/jumpstart) | Using SageMaker JumpStart | [notebook](./sagemaker-async-inference/jumpstart/src/notebook/async-jumpstart.ipynb) |
| Asynchronous Inference | [HuggingFace](./sagemaker-async-inference/hugging-face) | Using Hugging Face DLC | [notebook](./sagemaker-async-inference/hugging-face/src/notebook/async-hugging-face.ipynb) |
| Asynchronous Inference | [PyTorch](./sagemaker-async-inference/pytorch) | Using PyTorch DLC | [notebook](./sagemaker-async-inference/pytorch/src/notebook/async-pytorch.ipynb) |
| Real-time Inference | [SageMaker JumpStart](./sagemaker-realtime-inference/jumpstart) | Using SageMaker JumpStart | [notebook](./sagemaker-realtime-inference/jumpstart/src/notebook/realtime-jumpstart.ipynb) |
| Real-time Inference | [HuggingFace](./sagemaker-realtime-inference/hugging-face) | Using Hugging Face DLC | [notebook](./sagemaker-realtime-inference/hugging-face/src/notebook/realtime-hugging-face.ipynb) |
| Real-time Inference | [PyTorch](./sagemaker-realtime-inference/pytorch) | Using PyTorch DLC | [notebook](./sagemaker-realtime-inference/pytorch/src/notebook/realtime-pytorch.ipynb) |

Enjoy!

## References

 * [Amazon SageMaker Deploy models for inference](https://docs.aws.amazon.com/sagemaker/latest/dg/deploy-model.html)
