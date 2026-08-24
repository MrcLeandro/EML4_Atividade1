import boto3
import requests
import json
import os


S3_INPUT_BUCKET_NAME = os.environ.get('S3_INPUT_BUCKET_NAME')
S3_INPUT_FILE_KEY = 'urls.txt'

# --- Configuration for Output S3 
S3_OUTPUT_BUCKET_NAME = os.environ.get('S3_OUTPUT_BUCKET_NAME')
S3_OUTPUT_FILE_KEY = 'pokemon_data.json' 

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    extracted_pokemon_data = [] # Changed to store dictionaries of data

    try:
        # 1. Download the urls.txt file from S3
        response = s3_client.get_object(Bucket=S3_INPUT_BUCKET_NAME, Key=S3_INPUT_FILE_KEY)
        urls_content = response['Body'].read().decode('utf-8')
        urls = urls_content.strip().split('\n')

        print(f"Successfully retrieved {len(urls)} URLs from S3 from bucket {S3_INPUT_BUCKET_NAME}.")

        # 2. Iterate through each URL and make an API call
        for url in urls:
            if url.strip(): # Ensure URL is not empty
                try:
                    print(f"Fetching data from: {url.strip()}")
                    api_response = requests.get(url.strip())
                    api_response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
                    data = api_response.json()

                    # Prepare a dictionary for this Pokemon's data
                    pokemon_info = {}

                    # 3. Extract the requested fields
                    pokemon_info['name'] = data.get("name")
                    pokemon_info['id'] = data.get("id")
                    pokemon_info['height'] = data.get("height")
                    pokemon_info['weight'] = data.get("weight")

                    # Extract names from subitems within 'types'
                    type_names = []
                    types = data.get("types", [])
                    for item in types:
                        if 'type' in item and 'name' in item['type']:
                            type_names.append(item['type']['name'])
                    pokemon_info['types'] = type_names

                    # Count occurrences of the word "move" in the entire JSON response
                    json_string = json.dumps(data).lower()
                    pokemon_info['move_count'] = json_string.count("move")

                    extracted_pokemon_data.append(pokemon_info)
                    print(f"Extracted data for: {pokemon_info['name']}")

                except requests.exceptions.RequestException as e:
                    print(f"Error fetching data from {url.strip()}: {e}")
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {url.strip()}: {e}")
                except Exception as e:
                    print(f"An error occurred during data extraction for {url.strip()}: {e}")

    except s3_client.exceptions.NoSuchKey:
        print(f"Error: The input file {S3_INPUT_FILE_KEY} was not found in bucket {S3_INPUT_BUCKET_NAME}.")
        return {
            'statusCode': 404,
            'body': json.dumps(f'Input file {S3_INPUT_FILE_KEY} not found in S3 bucket {S3_INPUT_BUCKET_NAME}.')
        }
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {e}')
        }

    # 4. Write the extracted data to the output S3 bucket
    try:
        output_json_data = json.dumps(extracted_pokemon_data, indent=2)
        s3_client.put_object(
            Bucket=S3_OUTPUT_BUCKET_NAME,
            Key=S3_OUTPUT_FILE_KEY,
            Body=output_json_data,
            ContentType='application/json'
        )
        print(f"Successfully wrote {len(extracted_pokemon_data)} records to s3://{S3_OUTPUT_BUCKET_NAME}/{S3_OUTPUT_FILE_KEY}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data successfully extracted and written to S3.',
                'output_s3_location': f's3://{S3_OUTPUT_BUCKET_NAME}/{S3_OUTPUT_FILE_KEY}',
                'count': len(extracted_pokemon_data)
            })
        }
    except Exception as e:
        print(f"Error writing data to output S3 bucket {S3_OUTPUT_BUCKET_NAME}: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error writing output to S3: {e}')
        }
