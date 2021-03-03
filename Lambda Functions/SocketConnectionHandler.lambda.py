import json
import boto3
dynamodb = boto3.client('dynamodb')

TABLE_NAME = "SocketConnections"

def lambda_handler(event, context):
    connectionId = event['requestContext']['connectionId']
    if event['requestContext']['eventType'] == 'CONNECT':
        
        deviceId = event['queryStringParameters']['deviceId']
        dynamodb.put_item(
            TableName = TABLE_NAME,
            Item = {
                'connectionId': { 'S': str(connectionId) },
                'deviceId': { 'S': str(deviceId) }
            }
        )
        return {
            'statusCode': 200, 'body': 'Connected.'
        }

    if event['requestContext']['eventType'] == 'DISCONNECT':
        dynamodb.delete_item(
            TableName = TABLE_NAME,
            Key = { 
                'connectionId': {
                    'S': str(connectionId) 
                }
            }
        )
        return { 
            'statusCode': 200, 
            'body': 'Disconnected.'
        }