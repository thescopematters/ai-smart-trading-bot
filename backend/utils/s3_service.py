import os
import uuid
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("S3Service")

class S3Service:
    def __init__(self):
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "ai-trading-bot-s3")
        
        self.s3_client = None
        if self.aws_access_key and self.aws_secret_key:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.region
                )
                logger.info("S3 Service client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
        else:
            logger.warning("AWS credentials not fully configured in environment. S3 features will be disabled.")

    def upload_file_to_s3(self, local_file_path: str, original_file_name: str) -> dict:
        """
        Uploads a local file to S3 under documents/{uuid}_{filename}.
        Returns a dictionary with s3_url and s3_key, or raises an Exception on failure.
        """
        if not self.s3_client:
            raise Exception("S3 client is not initialized. Check your environment variables.")

        # Create unique key to prevent name collisions
        file_uuid = str(uuid.uuid4())
        s3_key = f"documents/{file_uuid}_{original_file_name}"

        try:
            logger.info(f"Uploading {local_file_path} to S3 bucket {self.bucket_name} as {s3_key}...")
            self.s3_client.upload_file(local_file_path, self.bucket_name, s3_key)
            
            # Construct S3 URL (standard regional format)
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            logger.info(f"Successfully uploaded file to S3: {s3_url}")
            
            return {
                "s3_url": s3_url,
                "s3_key": s3_key
            }
        except ClientError as e:
            logger.error(f"AWS ClientError during upload: {e}")
            raise e
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise e

    def delete_file_from_s3(self, s3_key: str) -> bool:
        """
        Deletes a file from the S3 bucket using its key.
        Handles failures gracefully and returns a boolean status.
        """
        if not self.s3_client:
            logger.warning("Cannot delete from S3: client not initialized.")
            return False

        if not s3_key:
            logger.warning("No s3_key provided for S3 deletion.")
            return False

        try:
            logger.info(f"Deleting S3 key {s3_key} from bucket {self.bucket_name}...")
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Successfully deleted S3 key {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"AWS ClientError during S3 deletion of {s3_key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete S3 key {s3_key}: {e}")
            return False

    def generate_presigned_url(self, s3_key: str, expiry: int = None) -> str:
        """
        Generates a temporary pre-signed URL for private bucket access.
        """
        if not self.s3_client:
            logger.warning("S3 client not initialized. Cannot generate pre-signed URL.")
            return ""

        if not s3_key:
            logger.warning("No s3_key provided for pre-signed URL generation.")
            return ""

        if expiry is None:
            try:
                expiry = int(os.getenv("S3_PRESIGNED_URL_EXPIRY", 3600))
            except ValueError:
                expiry = 3600

        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiry
            )
            return url
        except ClientError as e:
            logger.error(f"AWS ClientError generating pre-signed URL for {s3_key}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Failed to generate pre-signed URL for {s3_key}: {e}")
            return ""

s3_service = S3Service()
