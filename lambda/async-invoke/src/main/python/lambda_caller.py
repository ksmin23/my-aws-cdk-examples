#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json

def lambda_handler(event, context):
  print(json.dumps(event))

  record = event['Records'][0]['Sns']
  sns_subject = record['Subject']
  if sns_subject == 'On_Failure':
    raise RuntimeError('LambdaDestinationsOnFailure')

  return {
      'statusCode': 200,
      'body': json.dumps('Hello from Lambda!')
  }


if __name__ == '__main__':
  event = {
    "Records": [
        {
            "EventSource": "aws:sns",
            "EventVersion": "1.0",
            "EventSubscriptionArn": "arn:aws:sns:us-east-1:819320734790:LambdaSourceEvent:ee80f17a-bd9f-4378-bfe4-9886b6981fb1",
            "Sns": {
                "Type": "Notification",
                "MessageId": "c9fec813-c180-5cca-8b61-91fa4e2d2d73",
                "TopicArn": "arn:aws:sns:us-east-1:819320734790:LambdaSourceEvent",
                "Subject": None,
                "Message": "Hello SNS!",
                "Timestamp": "2021-10-20T03:30:53.899Z",
                "SignatureVersion": "1",
                "Signature": "NRnKOkZ9CORAKwubzJPNQgB/OF+1zRrz1Gz+e2oDOQvdsy0ribQu7E0vEgOpWHFpq2eS0tmjQmHz4TN9DBv9uBD0MVLD1ggPW216XNoU2GJvNut1SovllSb1dIcAkEKMB1/p9gniguKPx+Zvb56sDrDbQEc/yRNXoYwUjgdAWBZ1Z2soTMiLtR0Ce8QYDVKn/ZSRvvtceZ1nYfJYNC0LQHk609znM4JXqmF/Ojr1AJ1eQMB2nnmnJ51cnePkWVy6O2CIRe+A9ET7MpCrQc87a2rKDiYAoN6PqZBvFsOuEhtiLkp5+Dw0YQh3M26LTP48vYicMcMuJ3l/VTYLcJ/Y6g==",
                "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-7ff5318490ec183fbaddaa2a969abfda.pem",
                "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:819320734790:LambdaSourceEvent:ee80f17a-bd9f-4378-bfe4-9886b6981fb1",
                "MessageAttributes": {}
            }
        }
    ]
  }

  lambda_handler(event, {})

