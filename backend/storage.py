# storage.py
import boto3
import os
s3 = boto3.client('s3',
                  aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                  region_name=os.environ.get('AWS_REGION'))

BUCKET = os.environ.get('S3_BUCKET')

def upload_bytes_to_s3(key, bytes_data):
    s3.put_object(Bucket=BUCKET, Key=key, Body=bytes_data, ServerSideEncryption='AES256')
    return f"s3://{BUCKET}/{key}"

def presigned_url_for_get(key, expires_in=300):
    return s3.generate_presigned_url('get_object', Params={'Bucket': BUCKET, 'Key': key}, ExpiresIn=expires_in)
