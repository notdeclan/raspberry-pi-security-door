import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

TABLE_NAME = "SocketConnections"

dynamodb = boto3.resource('dynamodb')
api = boto3.client(
    'apigatewaymanagementapi', 
    endpoint_url = "https://e15jdyr5ml.execute-api.us-east-1.amazonaws.com/production/"
)

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)
    response = table.scan(FilterExpression=Attr("deviceId").eq(event['deviceId']))
    connections = response['Items']
    
    for connection in connections:
        connectionId = connection['connectionId']
        try:
            api.post_to_connection(
                ConnectionId = str(connectionId), 
                Data = json.dumps(event)
            )
            print("Send to: %s" % connectionId)
        except Exception as e:
            print("Failed to send to: %s" % connectionId)
        
    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }
