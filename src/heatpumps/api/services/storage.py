"""
Google Cloud Storage service for report management.

This module provides functions for uploading, downloading, and managing
simulation reports in Google Cloud Storage.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from google.cloud import storage
from google.api_core import exceptions as gcp_exceptions

logger = logging.getLogger(__name__)


class StorageService:
    """Service class for Google Cloud Storage operations."""

    def __init__(self, bucket_name: str, project_id: str, location: str = "europe-west2"):
        """
        Initialize the Storage Service.

        Args:
            bucket_name: Name of the GCS bucket
            project_id: GCP project ID
            location: GCS bucket location (default: europe-west2)
        """
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.location = location
        self._client = None
        self._bucket = None

    def _get_client(self) -> storage.Client:
        """Get or create storage client (lazy initialization)."""
        if self._client is None:
            try:
                self._client = storage.Client(project=self.project_id)
                logger.info(f"Initialized GCS client for project: {self.project_id}")
            except Exception as e:
                logger.error(f"Failed to initialize GCS client: {e}")
                raise
        return self._client

    def _get_bucket(self) -> storage.Bucket:
        """Get or create bucket reference (lazy initialization)."""
        if self._bucket is None:
            client = self._get_client()
            try:
                self._bucket = client.bucket(self.bucket_name)
                # Verify bucket exists
                if not self._bucket.exists():
                    raise ValueError(
                        f"Bucket '{self.bucket_name}' does not exist. "
                        f"Please create it first using setup_gcs_bucket.sh"
                    )
                logger.info(f"Connected to GCS bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to access bucket '{self.bucket_name}': {e}")
                raise
        return self._bucket

    def _get_blob_path(self, report_id: str) -> str:
        """
        Generate blob path for a report.

        Args:
            report_id: Unique report identifier

        Returns:
            Blob path in format: reports/YYYY-MM/report_id.json
        """
        now = datetime.utcnow()
        folder = f"reports/{now.year:04d}-{now.month:02d}"
        return f"{folder}/{report_id}.json"

    def _generate_signed_url_v4(
        self,
        blob: storage.Blob,
        expiration_days: int = 7
    ) -> str:
        """
        Generate a signed URL using IAM-based signing (works with compute credentials).

        Args:
            blob: GCS blob object
            expiration_days: Number of days until URL expires

        Returns:
            Signed URL string
        """
        try:
            # Try standard signing first (works with service account JSON keys)
            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(days=expiration_days),
                method="GET"
            )
        except Exception as e:
            # If standard signing fails (no private key), fall back to public URL
            # Note: This requires the bucket to have public access or the object to be public
            logger.warning(
                f"Cannot generate signed URL (no private key): {e}. "
                f"Falling back to public URL. For production, use a service account with a JSON key."
            )
            # Return the public URL (requires bucket/object to be publicly readable)
            return blob.public_url

    async def upload_json(
        self,
        data: Dict[str, Any],
        report_id: str,
        content_type: str = "application/json"
    ) -> Dict[str, str]:
        """
        Upload JSON data to Cloud Storage.

        Args:
            data: Dictionary to upload as JSON
            report_id: Unique report identifier
            content_type: MIME type (default: application/json)

        Returns:
            Dictionary with storage_url and signed_url

        Raises:
            Exception: If upload fails
        """
        try:
            bucket = self._get_bucket()
            blob_path = self._get_blob_path(report_id)
            blob = bucket.blob(blob_path)

            # Convert data to JSON string
            json_data = json.dumps(data, indent=2)

            # Upload with metadata
            blob.upload_from_string(
                json_data,
                content_type=content_type
            )

            # Set metadata
            blob.metadata = {
                "report_id": report_id,
                "created_at": datetime.utcnow().isoformat(),
                "content_type": content_type
            }
            blob.patch()

            # Generate public URL (bucket must have public access enabled)
            # Note: Cannot use signed URLs with compute credentials (no private key)
            signed_url = blob.public_url

            storage_url = f"gs://{self.bucket_name}/{blob_path}"

            logger.info(f"Successfully uploaded report {report_id} to {storage_url}")

            return {
                "storage_url": storage_url,
                "signed_url": signed_url,
                "blob_path": blob_path
            }

        except Exception as e:
            logger.error(f"Failed to upload report {report_id}: {e}")
            raise

    async def download_json(self, report_id: str) -> Dict[str, Any]:
        """
        Download JSON data from Cloud Storage.

        Args:
            report_id: Unique report identifier

        Returns:
            Dictionary containing the report data

        Raises:
            FileNotFoundError: If report doesn't exist
            Exception: If download fails
        """
        try:
            bucket = self._get_bucket()
            blob_path = self._get_blob_path(report_id)
            blob = bucket.blob(blob_path)

            if not blob.exists():
                raise FileNotFoundError(f"Report {report_id} not found")

            # Download as string and parse JSON
            json_data = blob.download_as_text()
            data = json.loads(json_data)

            logger.info(f"Successfully downloaded report {report_id}")
            return data

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to download report {report_id}: {e}")
            raise

    async def delete_report(self, report_id: str) -> bool:
        """
        Delete a report from Cloud Storage.

        Args:
            report_id: Unique report identifier

        Returns:
            True if deleted successfully, False if not found

        Raises:
            Exception: If deletion fails
        """
        try:
            bucket = self._get_bucket()
            blob_path = self._get_blob_path(report_id)
            blob = bucket.blob(blob_path)

            if not blob.exists():
                logger.warning(f"Report {report_id} not found for deletion")
                return False

            blob.delete()
            logger.info(f"Successfully deleted report {report_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {e}")
            raise

    async def list_reports(
        self,
        limit: int = 100,
        prefix: str = "reports/"
    ) -> List[Dict[str, Any]]:
        """
        List reports in Cloud Storage.

        Args:
            limit: Maximum number of reports to return
            prefix: Blob prefix to filter by (default: "reports/")

        Returns:
            List of dictionaries containing report metadata

        Raises:
            Exception: If listing fails
        """
        try:
            bucket = self._get_bucket()
            blobs = bucket.list_blobs(prefix=prefix, max_results=limit)

            reports = []
            for blob in blobs:
                # Extract report_id from path (reports/YYYY-MM/report_id.json)
                path_parts = blob.name.split("/")
                if len(path_parts) >= 3 and blob.name.endswith(".json"):
                    report_id = path_parts[-1].replace(".json", "")

                    reports.append({
                        "report_id": report_id,
                        "blob_path": blob.name,
                        "size_bytes": blob.size,
                        "created_at": blob.time_created.isoformat() if blob.time_created else None,
                        "updated_at": blob.updated.isoformat() if blob.updated else None,
                        "metadata": blob.metadata or {}
                    })

            logger.info(f"Listed {len(reports)} reports")
            return reports

        except Exception as e:
            logger.error(f"Failed to list reports: {e}")
            raise

    async def get_signed_url(
        self,
        report_id: str,
        expiration_days: int = 7
    ) -> str:
        """
        Generate a signed URL for a report.

        Args:
            report_id: Unique report identifier
            expiration_days: Number of days until URL expires (default: 7)

        Returns:
            Signed URL string

        Raises:
            FileNotFoundError: If report doesn't exist
            Exception: If URL generation fails
        """
        try:
            bucket = self._get_bucket()
            blob_path = self._get_blob_path(report_id)
            blob = bucket.blob(blob_path)

            if not blob.exists():
                raise FileNotFoundError(f"Report {report_id} not found")

            signed_url = self._generate_signed_url_v4(blob, expiration_days=expiration_days)

            logger.info(f"Generated signed URL for report {report_id}")
            return signed_url

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {report_id}: {e}")
            raise
