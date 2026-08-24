import boto3
import json
import os
import pymysql 
pymysql.install_as_MySQLdb()
import MySQLdb

DB_HOST_SQS = os.environ.get('DB_HOST_SQS')
DB_USER_SQS = os.environ.get('DB_USER_SQS')
DB_PASSWORD_SQS = os.environ.get('DB_PASSWORD_SQS')
DB_NAME_SQS = os.environ.get('DB_NAME_SQS')
DB_PORT_SQS = int(os.environ.get('DB_PORT_SQS'))

# --- SQS Configuration 
# If the Lambda is triggered by SQS, the event contains the messages.

SQS_QUEUE_URL_FOR_DELETION = os.environ.get('SQS_QUEUE_URL_FOR_DELETION', 'https://sqs.your-region.amazonaws.com/your-account-id/your-sqs-queue-name')

def insert_data_from_sqs_to_mariadb(data_list):
    conn = None
    cursor = None
    try:
        # Establish database connection
        conn = MySQLdb.connect(
            host=DB_HOST_SQS,
            user=DB_USER_SQS,
            passwd=DB_PASSWORD_SQS,
            db=DB_NAME_SQS,
            port=DB_PORT_SQS,
            connect_timeout=10 # Add a connection timeout
        )
        cursor = conn.cursor()

       
        insert_sql = """
        INSERT INTO processed_sqs_data (id, name, height, weight, types, move_count, timestamp)
        VALUES (%s, %s, %s,, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            heigth = VALUES(height),
            weight = VALUES(weight),
            move_count = VALUES(move_count),
            types = VALUES(types),
            timestamp = VALUES(timestamp)
        """

        inserted_count = 0
        for item in data_list:
            try:
                # Assuming 'item' is a dict with 'id', 'name', 'value'
                # Adjust these keys according to your SQS message format
                data_to_insert = (
                    item.get('id'),
                    item.get('name'),
                    item.get('height'),
                    item.get('weight'),
                    item.get('types'),
                    item.get('move_count')
                )
                cursor.execute(insert_sql, data_to_insert)
                inserted_count += 1
            except Exception as e:
                print(f"Error inserting record {item}: {e}")
                # Decide whether to continue or re-raise
                conn.rollback() # Rollback current transaction if an item fails

        conn.commit() # Commit all successful insertions
        print(f"Successfully inserted/updated {inserted_count} records into MariaDB.")
        return inserted_count

    except MySQLdb.Error as err:
        print(f"Error connecting to or inserting into MariaDB: {err}")
        if conn:
            conn.rollback() # Rollback in case of a connection or major transaction error
        raise err
    except Exception as e:
        print(f"An unexpected error occurred during database operation: {e}")
        raise e
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if conn and conn.open:
            conn.close()
            print("MariaDB connection closed.")

def lambda_handler(event, context):
    sqs_client = boto3.client('sqs')
    messages_processed = 0
    messages_failed = 0
    batch_item_failures = []

    print(f"Received {len(event['Records'])} messages from SQS.")

    for record in event['Records']:
        message_body = record['body']
        receipt_handle = record['receiptHandle']

        try:
            # Assuming the SQS message body is a JSON string
            parsed_data = json.loads(message_body)
            
            # If the SQS message contains a list of items, process each one
            if isinstance(parsed_data, list):
                inserted_count = insert_data_from_sqs_to_mariadb(parsed_data)
            else:
                # If it's a single JSON object, wrap it in a list for the helper function
                inserted_count = insert_data_from_sqs_to_mariadb([parsed_data])
            
            messages_processed += inserted_count
            # If successful, the message is automatically deleted by SQS Lambda trigger
            # If not using a Lambda SQS trigger, you'd manually delete with sqs_client.delete_message()
            
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from SQS message: {e}. Message body: {message_body}")
            messages_failed += 1
            batch_item_failures.append({'itemIdentifier': record['messageId']})
        except Exception as e:
            print(f"Error processing SQS message for MariaDB insertion: {e}. Message body: {message_body}")
            messages_failed += 1
            batch_item_failures.append({'itemIdentifier': record['messageId']})

    print(f"Finished processing SQS batch. Processed: {messages_processed}, Failed: {messages_failed}")
    
    # For SQS event source mapping with partial batch failure
    return {
        'batchItemFailures': batch_item_failures
    }
    
