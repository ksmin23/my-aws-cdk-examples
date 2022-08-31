#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

from typing import Any, Dict, List
import sys
import os
import traceback
from datetime import datetime

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.metrics import Metrics
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext
tracer = Tracer()
logger = Logger()
metrics = Metrics()

@tracer.capture_lambda_handler
@metrics.log_metrics
def lambda_handler(event: Dict[str, Any], _: LambdaContext) -> List[str]:
  now = datetime.now()
  now_str = now.strftime("%Y-%m-%d %H:%M:%S")
  logger.info(f"[INFO] Hello Scheduled Lambda at {now_str}")

if __name__ == '__main__':
  event = {}
  lambda_handler(event, {})

