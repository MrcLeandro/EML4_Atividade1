import boto3
import json
import os

# --- Configuração de Entrada S3 

S3_INPUT_BUCKET_NAME_SQS = os.environ.get('S3_INPUT_BUCKET_NAME_SQS')  
S3_INPUT_FILE_KEY_SQS = 'pokemon_data.json' 

# --- Configuração da Fila SQS 
SQS_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/749680934020/Minha_Fila' 

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    sqs_client = boto3.client('sqs')
    
    try:
        # 1. Baixar o arquivo JSON do S3
        print(f"Baixando {S3_INPUT_FILE_KEY_SQS} do S3 bucket {S3_INPUT_BUCKET_NAME_SQS}...")
        response = s3_client.get_object(Bucket=S3_INPUT_BUCKET_NAME_SQS, Key=S3_INPUT_FILE_KEY_SQS)
        json_content = response['Body'].read().decode('utf-8')
        data = json.loads(json_content)

        print(f"Arquivo JSON baixado e analisado com sucesso.")

        messages_sent_count = 0
        
        # 2. Enviar dados para a fila SQS
        if isinstance(data, list):
            print(f"Detectado array JSON. Enviando {len(data)} registros para SQS...")
            for record in data:
                sqs_client.send_message(
                    QueueUrl=SQS_QUEUE_URL,
                    MessageBody=json.dumps(record) # Cada registro é uma mensagem SQS
                )
                messages_sent_count += 1
        elif isinstance(data, dict):
            print(f"Detectado objeto JSON único. Enviando para SQS...")
            sqs_client.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps(data) # O objeto inteiro é uma mensagem SQS
            )
            messages_sent_count += 1
        else:
            raise ValueError("O conteúdo do arquivo JSON não é um objeto ou lista JSON válido.")

        print(f"{messages_sent_count} mensagens enviadas com sucesso para a fila SQS.")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'{messages_sent_count} registros enviados para SQS.',
                's3_input_file': f's3://{S3_INPUT_BUCKET_NAME_SQS}/{S3_INPUT_FILE_KEY_SQS}',
                'sqs_queue_url': SQS_QUEUE_URL,
                'messages_sent': messages_sent_count
            })
        }

    except s3_client.exceptions.NoSuchKey:
        print(f"Erro: O arquivo de entrada {S3_INPUT_FILE_KEY_SQS} não foi encontrado no bucket {S3_INPUT_BUCKET_NAME_SQS}.")
        return {
            'statusCode': 404,
            'body': json.dumps(f'Arquivo de entrada {S3_INPUT_FILE_KEY_SQS} não encontrado no bucket S3 {S3_INPUT_BUCKET_NAME_SQS}.')
        }
    except json.JSONDecodeError as e:
        print(f"Erro ao analisar o JSON do arquivo S3: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps(f'Erro de formato JSON no arquivo S3: {e}')
        }
    except ValueError as e:
        print(f"Erro de valor: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps(f'Erro de valor: {e}')
        }
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Ocorreu um erro: {e}')
        }
