"""
App Distribution API Endpoints
=============================

This module provides API endpoints for Flutter app distribution:
- APK file management and distribution
- Version control and update checking
- Device-specific app downloads
- Auto-update configuration
"""

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Response, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional, Dict, Any, BinaryIO
from datetime import date, datetime, timedelta
import logging
import uuid
import os
import hashlib
import json
import aiofiles
from pathlib import Path

from app.models_ad_slots import AppUpdateInfo
from app.models import Permission
from app.auth_service import get_current_user
from app.rbac_service import rbac_service
from app.database_service import db_service

router = APIRouter(prefix="/api/app-distribution", tags=["App Distribution"])
logger = logging.getLogger(__name__)

# Configuration
APK_STORAGE_PATH = os.getenv("APK_STORAGE_PATH", "./storage/apks")
MAX_APK_SIZE = 100 * 1024 * 1024  # 100MB
SUPPORTED_ARCHITECTURES = ["arm64-v8a", "armeabi-v7a", "universal"]


# ==================== APK UPLOAD & MANAGEMENT ====================

@router.post("/upload-apk", response_model=Dict[str, Any])
async def upload_apk(
    version: str,
    build_number: str,
    architecture: str = "universal",
    change_log: str = "",
    is_forced: bool = False,
    min_os_version: str = "21",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    apk_file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user)
):
    """Upload a new APK version"""
    try:
        # Check permissions - only super users can upload APKs
        if current_user.get("user_type") != "SUPER_USER":
            raise HTTPException(status_code=403, detail="Only platform administrators can upload APKs")

        # Validate file
        if not apk_file.filename.endswith('.apk'):
            raise HTTPException(status_code=400, detail="File must be an APK")

        if apk_file.size and apk_file.size > MAX_APK_SIZE:
            raise HTTPException(status_code=400, detail=f"File size exceeds {MAX_APK_SIZE // (1024*1024)}MB limit")

        if architecture not in SUPPORTED_ARCHITECTURES:
            raise HTTPException(status_code=400, detail=f"Unsupported architecture. Must be one of: {SUPPORTED_ARCHITECTURES}")

        logger.info(f"Uploading APK v{version} ({build_number}) for {architecture}")

        # Create storage directory
        storage_dir = Path(APK_STORAGE_PATH)
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"adara_player_v{version}_{build_number}_{architecture}.apk"
        file_path = storage_dir / filename

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await apk_file.read()
            await f.write(content)

        # Calculate checksum
        checksum = hashlib.sha256(content).hexdigest()
        file_size_mb = len(content) // (1024 * 1024)

        # Create APK record
        apk_record = {
            "id": str(uuid.uuid4()),
            "version": version,
            "build_number": build_number,
            "architecture": architecture,
            "filename": filename,
            "file_path": str(file_path),
            "file_size_mb": file_size_mb,
            "checksum": checksum,
            "change_log": change_log,
            "is_forced": is_forced,
            "min_os_version": min_os_version,
            "upload_date": datetime.utcnow(),
            "uploaded_by": current_user["id"],
            "download_count": 0,
            "is_active": True
        }

        # Save to database
        result = await db_service.create_record("app_versions", apk_record)
        if not result.success:
            # Clean up file if database save fails
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=500, detail=f"Failed to save APK record: {result.error}")

        # Generate download URL
        download_url = f"/api/app-distribution/download/{apk_record['id']}"

        # Queue background tasks
        background_tasks.add_task(_analyze_apk_metadata, str(file_path), apk_record["id"])
        background_tasks.add_task(_notify_devices_of_update, apk_record["id"])

        logger.info(f"APK uploaded successfully: {filename}")

        return {
            "message": "APK uploaded successfully",
            "apk_id": apk_record["id"],
            "version": version,
            "build_number": build_number,
            "architecture": architecture,
            "download_url": download_url,
            "file_size_mb": file_size_mb,
            "checksum": checksum
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading APK: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/versions", response_model=List[Dict[str, Any]])
async def list_app_versions(
    architecture: Optional[str] = Query(None),
    active_only: bool = Query(True),
    current_user: Dict = Depends(get_current_user)
):
    """List available app versions"""
    try:
        # Build filters
        filters = {}
        if architecture:
            filters["architecture"] = architecture
        if active_only:
            filters["is_active"] = True

        result = await db_service.query_records("app_versions", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve app versions")

        # Sort by version and build number (newest first)
        versions = sorted(result.data, key=lambda x: (x.get("version", ""), x.get("build_number", "")), reverse=True)

        # Remove file paths from public response (security)
        for version in versions:
            version.pop("file_path", None)

        return versions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing app versions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/versions/{version_id}", response_model=Dict[str, Any])
async def get_app_version(
    version_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get specific app version details"""
    try:
        result = await db_service.get_record("app_versions", version_id)
        if not result.success:
            raise HTTPException(status_code=404, detail="App version not found")

        version = result.data

        # Remove sensitive information for non-admin users
        if current_user.get("user_type") != "SUPER_USER":
            version.pop("file_path", None)
            version.pop("uploaded_by", None)

        return version

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting app version: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== APK DOWNLOAD ====================

@router.get("/download/{version_id}")
async def download_apk(
    version_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Download APK file"""
    try:
        # Get version record
        result = await db_service.get_record("app_versions", version_id)
        if not result.success:
            raise HTTPException(status_code=404, detail="App version not found")

        version = result.data

        if not version.get("is_active", False):
            raise HTTPException(status_code=404, detail="App version is not active")

        file_path = Path(version.get("file_path", ""))
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="APK file not found on disk")

        # Increment download counter
        await _increment_download_count(version_id)

        # Log download
        await _log_apk_download(version_id, current_user)

        # Return file
        return FileResponse(
            path=str(file_path),
            filename=version.get("filename", "app.apk"),
            media_type="application/vnd.android.package-archive",
            headers={
                "Content-Disposition": f"attachment; filename=\"{version.get('filename', 'app.apk')}\"",
                "X-Content-SHA256": version.get("checksum", ""),
                "X-File-Size": str(version.get("file_size_mb", 0) * 1024 * 1024)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading APK: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/download-url/{version_id}")
async def get_download_url(
    version_id: str,
    expires_hours: int = Query(24, ge=1, le=168),  # 1 hour to 7 days
    current_user: Dict = Depends(get_current_user)
):
    """Get temporary download URL for APK"""
    try:
        # Check if version exists
        result = await db_service.get_record("app_versions", version_id)
        if not result.success:
            raise HTTPException(status_code=404, detail="App version not found")

        version = result.data
        if not version.get("is_active", False):
            raise HTTPException(status_code=404, detail="App version is not active")

        # Generate temporary download token
        download_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

        # Store download token
        token_record = {
            "id": download_token,
            "version_id": version_id,
            "created_by": current_user["id"],
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "used": False
        }

        token_result = await db_service.create_record("download_tokens", token_record)
        if not token_result.success:
            raise HTTPException(status_code=500, detail="Failed to create download token")

        download_url = f"/api/app-distribution/download-with-token/{download_token}"

        return {
            "download_url": download_url,
            "expires_at": expires_at.isoformat(),
            "version": version.get("version"),
            "build_number": version.get("build_number"),
            "architecture": version.get("architecture"),
            "file_size_mb": version.get("file_size_mb")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/download-with-token/{token}")
async def download_apk_with_token(token: str):
    """Download APK using temporary token"""
    try:
        # Get and validate token
        token_result = await db_service.get_record("download_tokens", token)
        if not token_result.success:
            raise HTTPException(status_code=404, detail="Invalid download token")

        token_data = token_result.data

        if token_data.get("used", False):
            raise HTTPException(status_code=410, detail="Download token has already been used")

        if datetime.fromisoformat(token_data.get("expires_at", "")) < datetime.utcnow():
            raise HTTPException(status_code=410, detail="Download token has expired")

        # Get version
        version_result = await db_service.get_record("app_versions", token_data["version_id"])
        if not version_result.success:
            raise HTTPException(status_code=404, detail="App version not found")

        version = version_result.data
        file_path = Path(version.get("file_path", ""))

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="APK file not found")

        # Mark token as used
        await db_service.update_record("download_tokens", token, {"used": True, "used_at": datetime.utcnow()})

        # Increment download counter
        await _increment_download_count(version["id"])

        # Return file
        return FileResponse(
            path=str(file_path),
            filename=version.get("filename", "app.apk"),
            media_type="application/vnd.android.package-archive",
            headers={
                "Content-Disposition": f"attachment; filename=\"{version.get('filename', 'app.apk')}\"",
                "X-Content-SHA256": version.get("checksum", "")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading APK with token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== UPDATE CHECKING ====================

@router.get("/check-update")
async def check_for_updates(
    current_version: str = Query(...),
    current_build_number: str = Query(...),
    architecture: str = Query("universal"),
    device_id: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """Check for app updates"""
    try:
        logger.info(f"Checking updates for v{current_version} ({current_build_number}) on {architecture}")

        # Find latest version for architecture
        filters = {
            "architecture": {"$in": [architecture, "universal"]},
            "is_active": True
        }

        result = await db_service.query_records("app_versions", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to check for updates")

        if not result.data:
            return {"update_available": False, "message": "No versions available"}

        # Sort by version and build number to get latest
        latest_version = sorted(
            result.data,
            key=lambda x: (x.get("version", ""), int(x.get("build_number", "0"))),
            reverse=True
        )[0]

        # Compare versions
        is_newer = _is_newer_version(
            latest_version.get("version", ""),
            latest_version.get("build_number", ""),
            current_version,
            current_build_number
        )

        if not is_newer:
            return {
                "update_available": False,
                "message": "App is up to date",
                "current_version": current_version,
                "current_build_number": current_build_number
            }

        # Create update info
        update_info = AppUpdateInfo(
            version=latest_version.get("version", ""),
            build_number=latest_version.get("build_number", ""),
            download_url=f"/api/app-distribution/download/{latest_version['id']}",
            change_log=latest_version.get("change_log", ""),
            is_forced=latest_version.get("is_forced", False),
            release_date=datetime.fromisoformat(latest_version.get("upload_date", "")),
            file_size_mb=latest_version.get("file_size_mb", 0),
            checksum=latest_version.get("checksum", "")
        )

        # Log update check
        if device_id:
            await _log_update_check(device_id, current_version, latest_version.get("version", ""), is_newer)

        return {
            "update_available": True,
            "update_info": update_info.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== UPDATE MANAGEMENT ====================

@router.post("/versions/{version_id}/activate", response_model=Dict[str, Any])
async def activate_version(
    version_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Activate an app version"""
    try:
        # Check permissions
        if current_user.get("user_type") != "SUPER_USER":
            raise HTTPException(status_code=403, detail="Only platform administrators can activate versions")

        # Get version
        result = await db_service.get_record("app_versions", version_id)
        if not result.success:
            raise HTTPException(status_code=404, detail="App version not found")

        # Activate version
        update_result = await db_service.update_record("app_versions", version_id, {
            "is_active": True,
            "activated_at": datetime.utcnow(),
            "activated_by": current_user["id"]
        })

        if not update_result.success:
            raise HTTPException(status_code=500, detail="Failed to activate version")

        logger.info(f"App version activated: {version_id} by {current_user['id']}")

        return {
            "message": "Version activated successfully",
            "version_id": version_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating version: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/versions/{version_id}/deactivate", response_model=Dict[str, Any])
async def deactivate_version(
    version_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Deactivate an app version"""
    try:
        # Check permissions
        if current_user.get("user_type") != "SUPER_USER":
            raise HTTPException(status_code=403, detail="Only platform administrators can deactivate versions")

        # Deactivate version
        update_result = await db_service.update_record("app_versions", version_id, {
            "is_active": False,
            "deactivated_at": datetime.utcnow(),
            "deactivated_by": current_user["id"]
        })

        if not update_result.success:
            raise HTTPException(status_code=500, detail="Failed to deactivate version")

        logger.info(f"App version deactivated: {version_id} by {current_user['id']}")

        return {
            "message": "Version deactivated successfully",
            "version_id": version_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating version: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_distribution_statistics(
    days: int = Query(30, ge=1, le=365),
    current_user: Dict = Depends(get_current_user)
):
    """Get app distribution statistics"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "analytics",
            "view"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view statistics")

        # Get download statistics
        start_date = datetime.utcnow() - timedelta(days=days)

        download_filters = {
            "downloaded_at": {"$gte": start_date.isoformat()}
        }

        downloads_result = await db_service.query_records("apk_downloads", download_filters)
        downloads = downloads_result.data if downloads_result.success else []

        # Get versions statistics
        versions_result = await db_service.query_records("app_versions", {"is_active": True})
        versions = versions_result.data if versions_result.success else []

        # Calculate statistics
        total_downloads = len(downloads)
        unique_devices = len(set(d.get("device_id") for d in downloads if d.get("device_id")))

        version_downloads = {}
        for download in downloads:
            version = download.get("version", "unknown")
            version_downloads[version] = version_downloads.get(version, 0) + 1

        architecture_downloads = {}
        for download in downloads:
            arch = download.get("architecture", "unknown")
            architecture_downloads[arch] = architecture_downloads.get(arch, 0) + 1

        return {
            "period_days": days,
            "total_downloads": total_downloads,
            "unique_devices": unique_devices,
            "active_versions": len(versions),
            "downloads_by_version": version_downloads,
            "downloads_by_architecture": architecture_downloads,
            "latest_version": versions[0].get("version") if versions else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting distribution statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== HELPER FUNCTIONS ====================

def _is_newer_version(new_version: str, new_build: str, current_version: str, current_build: str) -> bool:
    """Check if new version is newer than current"""
    try:
        # Simple version comparison
        new_parts = [int(x) for x in new_version.split('.')]
        current_parts = [int(x) for x in current_version.split('.')]

        # Pad to same length
        max_len = max(len(new_parts), len(current_parts))
        new_parts.extend([0] * (max_len - len(new_parts)))
        current_parts.extend([0] * (max_len - len(current_parts)))

        # Compare version parts
        for new, current in zip(new_parts, current_parts):
            if new > current:
                return True
            elif new < current:
                return False

        # If versions are equal, compare build numbers
        return int(new_build) > int(current_build)

    except (ValueError, TypeError):
        # If version parsing fails, assume newer
        return True


async def _increment_download_count(version_id: str):
    """Increment download count for version"""
    try:
        version = await db_service.get_record("app_versions", version_id)
        if version.success:
            current_count = version.data.get("download_count", 0)
            await db_service.update_record("app_versions", version_id, {
                "download_count": current_count + 1,
                "last_downloaded": datetime.utcnow()
            })
    except Exception as e:
        logger.error(f"Error incrementing download count: {e}")


async def _log_apk_download(version_id: str, user: Dict):
    """Log APK download"""
    try:
        download_log = {
            "id": str(uuid.uuid4()),
            "version_id": version_id,
            "downloaded_by": user.get("id"),
            "user_company_id": user.get("company_id"),
            "downloaded_at": datetime.utcnow(),
            "user_agent": "",  # Would get from request headers
            "ip_address": "",  # Would get from request
        }

        await db_service.create_record("apk_downloads", download_log)
    except Exception as e:
        logger.error(f"Error logging APK download: {e}")


async def _log_update_check(device_id: str, current_version: str, latest_version: str, update_available: bool):
    """Log update check"""
    try:
        check_log = {
            "id": str(uuid.uuid4()),
            "device_id": device_id,
            "current_version": current_version,
            "latest_version": latest_version,
            "update_available": update_available,
            "checked_at": datetime.utcnow()
        }

        await db_service.create_record("update_checks", check_log)
    except Exception as e:
        logger.error(f"Error logging update check: {e}")


async def _analyze_apk_metadata(file_path: str, version_id: str):
    """Analyze APK metadata (background task)"""
    try:
        # This would use aapt or similar tool to extract APK metadata
        logger.info(f"Analyzing APK metadata for {file_path}")
        # Implementation would extract package name, permissions, etc.
    except Exception as e:
        logger.error(f"Error analyzing APK metadata: {e}")


async def _notify_devices_of_update(version_id: str):
    """Notify devices of new update (background task)"""
    try:
        logger.info(f"Notifying devices of update: {version_id}")
        # Implementation would send push notifications to devices
    except Exception as e:
        logger.error(f"Error notifying devices of update: {e}")