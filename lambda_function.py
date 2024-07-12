import json
import boto3
import base64
import uuid

dynamodb = boto3.client('dynamodb')
rekognition = boto3.client('rekognition')
dynamo_table = 'rekognitionAuth'

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
    
    try:
        print(json.dumps(event))
        
        http_method = event.get('httpMethod', 'POST' if 'body' in event else 'GET')
        
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps('CORS preflight response')
            }
        
        if http_method == 'POST':
            # Handle POST request
            body = json.loads(event['body'])
            
            userEmail = body.get('userEmail', '')
            base64_image = body.get('image', '')
            
            if not userEmail or not base64_image:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing userEmail or image in body'})
                }
            
            image_data = base64.b64decode(base64_image)
            
            item_id = str(uuid.uuid4())
            
            item = {
                'userEmail': {'S': userEmail},
                'image_data': {'B': image_data}
            }
            
            dynamodb.put_item(
                TableName=dynamo_table,
                Item=item
            )
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'Item successfully inserted', 'userEmail': userEmail})
            }
        
        elif http_method == 'GET':
            # Handle GET request
            query_params = event.get('queryStringParameters', {})
            userEmail = query_params.get('userEmail', '')
            base64_image = query_params.get('image', '')
            
            if not userEmail or not base64_image:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing userEmail or image in query parameters'})
                }
            
            image_data = base64.b64decode(base64_image)
            
            response = dynamodb.get_item(
                TableName='rekognitionAuth',
                Key={'userEmail': {'S': userEmail}}
            )
            
            if 'Item' not in response:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'No image found for the given email'})
                }
            
            stored_image_data = response['Item']['image_data']['B']
            
            rekognition_response = rekognition.compare_faces(
                SourceImage={'Bytes': image_data},
                TargetImage={'Bytes': stored_image_data},
                SimilarityThreshold=80
            )
            
            match_found = len(rekognition_response['FaceMatches']) > 0
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'match': match_found, 'rekognitionResponse': rekognition_response})
            }
        
        else:
            # Default case when 'httpMethod' is not provided
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid or missing HTTP method'})
            }
    
    except KeyError as e:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
