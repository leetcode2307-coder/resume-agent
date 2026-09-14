import os
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

USE_S3 = os.getenv("USE_S3_STORAGE", "false").lower() == "true"
S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")

def get_s3_client():
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

def upload_pdf_to_s3(file_path: str, object_name: str) -> bool:
    if not USE_S3 or not S3_BUCKET_NAME:
        return False
        
    s3_client = get_s3_client()
    try:
        s3_client.upload_file(
            file_path,
            S3_BUCKET_NAME,
            object_name,
            ExtraArgs={"ContentType": "application/pdf"}
        )
        logger.info(f"Uploaded {file_path} to s3://{S3_BUCKET_NAME}/{object_name}")
        return True
    except Exception as e:
        error_str = str(e)
        if "NoSuchBucket" in error_str:
            logger.info(f"Bucket {S3_BUCKET_NAME} does not exist. Attempting to create it...")
            try:
                region = os.getenv("AWS_REGION", "us-east-1")
                if region == "us-east-1":
                    s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
                else:
                    s3_client.create_bucket(
                        Bucket=S3_BUCKET_NAME,
                        CreateBucketConfiguration={"LocationConstraint": region}
                    )
                # Retry upload after creation
                s3_client.upload_file(
                    file_path,
                    S3_BUCKET_NAME,
                    object_name,
                    ExtraArgs={"ContentType": "application/pdf"}
                )
                logger.info(f"Uploaded {file_path} to s3://{S3_BUCKET_NAME}/{object_name}")
                return True
            except Exception as creation_error:
                logger.error(f"Failed to create bucket and upload: {creation_error}")
                return False
        else:
            logger.error(f"Failed to upload to S3: {e}")
            return False

def get_presigned_url(object_name: str, expiration=3600) -> str | None:
    if not USE_S3 or not S3_BUCKET_NAME:
        return None
        
    s3_client = get_s3_client()
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': object_name},
            ExpiresIn=expiration
        )
        return response
    except ClientError as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        return None
