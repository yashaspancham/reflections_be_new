import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()
s3_client = boto3.client('s3', region_name="ap-south-1")
BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME')

def list_s3_files(max_keys=50):
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, MaxKeys=max_keys)
        files = response.get('Contents', [])
        return [file['Key'] for file in files]
    except ClientError as e:
        print("error: ",e)



def write_to_file(file_path: str, content: str) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def read_from_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""
