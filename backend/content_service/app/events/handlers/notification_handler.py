"""
Notification Event Handler - Processes notifications in background
Reduces load on primary application by handling notification operations asynchronously
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from app.events.event_bus import EventHandler, Event, EventType
from app.database_service import db_service

logger = logging.getLogger(__name__)

class NotificationHandler(EventHandler):
    """Background handler for notification processing"""

    def __init__(self):
        super().__init__(
            name="notification_handler",
            event_types=[
                EventType.CONTENT_UPLOADED,
                EventType.CONTENT_AI_MODERATION_COMPLETED,
                EventType.CONTENT_APPROVED,
                EventType.CONTENT_REJECTED,
                EventType.CONTENT_DEPLOYED,
                EventType.DEVICE_REGISTERED,
                EventType.DEVICE_STATUS_CHANGED,
                EventType.SYSTEM_ERROR,
                EventType.USER_LOGIN
            ]
        )
        self._notification_templates = {
            "content_uploaded": {
                "title": "Content Uploaded",
                "message": "New content '{filename}' has been uploaded and is being processed.",
                "recipients": ["content_reviewers"],
                "urgency": "normal"
            },
            "content_approved": {
                "title": "Content Approved",
                "message": "Content '{filename}' has been approved and is ready for scheduling.",
                "recipients": ["content_editors", "content_owner"],
                "urgency": "normal"
            },
            "content_rejected": {
                "title": "Content Rejected",
                "message": "Content '{filename}' has been rejected. Reason: {rejection_reason}",
                "recipients": ["content_owner"],
                "urgency": "high"
            },
            "content_deployed": {
                "title": "Content Deployed",
                "message": "Content '{filename}' has been deployed to {device_count} devices.",
                "recipients": ["content_owner", "device_managers"],
                "urgency": "normal"
            },
            "device_registered": {
                "title": "New Device Registered",
                "message": "Device '{device_name}' has been registered and is ready for content.",
                "recipients": ["device_managers", "company_admins"],
                "urgency": "normal"
            },
            "device_error": {
                "title": "Device Error",
                "message": "Device '{device_name}' is experiencing issues: {error_message}",
                "recipients": ["device_managers", "technical_support"],
                "urgency": "high"
            },
            "ai_moderation_failed": {
                "title": "AI Moderation Failed",
                "message": "AI moderation failed for content '{filename}'. Human review required.",
                "recipients": ["content_reviewers", "technical_support"],
                "urgency": "high"
            }
        }

    async def handle(self, event: Event) -> bool:
        """Process notification event"""
        try:
            notification_type = self._get_notification_type(event)
            if not notification_type:
                return True  # Not all events need notifications

            # Create notification
            notification = await self._create_notification(event, notification_type)
            if notification:
                # Store notification
                await self._store_notification(notification)

                # Send real-time notification
                await self._send_real_time_notification(notification)

                # Handle urgent notifications
                if notification.get("urgency") == "high":
                    await self._handle_urgent_notification(notification)

            return True

        except Exception as e:
            logger.error(f"Notification handler error for event {event.event_id}: {e}")
            return False

    def _get_notification_type(self, event: Event) -> Optional[str]:
        """Determine notification type based on event"""
        event_to_notification = {
            EventType.CONTENT_UPLOADED: "content_uploaded",
            EventType.CONTENT_APPROVED: "content_approved",
            EventType.CONTENT_REJECTED: "content_rejected",
            EventType.CONTENT_DEPLOYED: "content_deployed",
            EventType.DEVICE_REGISTERED: "device_registered",
            EventType.DEVICE_STATUS_CHANGED: "device_error",  # Only for error status
            EventType.CONTENT_AI_MODERATION_COMPLETED: "ai_moderation_failed"  # Only for failures
        }

        notification_type = event_to_notification.get(event.event_type)

        # Special handling for conditional notifications
        if event.event_type == EventType.DEVICE_STATUS_CHANGED:
            device_status = event.payload.get("new_status")
            if device_status not in ["error", "maintenance"]:
                return None  # Only notify for problematic statuses

        if event.event_type == EventType.CONTENT_AI_MODERATION_COMPLETED:
            moderation_result = event.payload.get("decision")
            if moderation_result != "failed":
                return None  # Only notify for moderation failures

        return notification_type

    async def _create_notification(self, event: Event, notification_type: str) -> Optional[Dict[str, Any]]:
        """Create notification data structure"""
        try:
            template = self._notification_templates.get(notification_type)
            if not template:
                logger.warning(f"No template found for notification type: {notification_type}")
                return None

            # Get context data for message formatting
            context_data = await self._get_context_data(event)

            # Format message with context
            title = template["title"]
            message = template["message"].format(**context_data)

            # Get recipient user IDs
            recipients = await self._get_notification_recipients(
                event.company_id,
                template["recipients"],
                event
            )

            if not recipients:
                logger.info(f"No recipients found for {notification_type} notification")
                return None

            notification = {
                "id": f"notif_{event.event_id}",
                "type": notification_type,
                "title": title,
                "message": message,
                "company_id": event.company_id,
                "event_id": event.event_id,
                "correlation_id": event.correlation_id,
                "recipients": recipients,
                "urgency": template["urgency"],
                "created_at": datetime.utcnow(),
                "status": "pending",
                "context": {
                    "event_type": event.event_type.value,
                    "content_id": event.content_id,
                    "device_id": event.device_id,
                    "user_id": event.user_id,
                    **context_data
                }
            }

            return notification

        except Exception as e:
            logger.error(f"Failed to create notification for event {event.event_id}: {e}")
            return None

    async def _get_context_data(self, event: Event) -> Dict[str, Any]:
        """Get contextual data for notification formatting"""
        context = {}

        try:
            # Get content information
            if event.content_id:
                content = await db_service.get_document("content", {"_id": event.content_id})
                if content:
                    context.update({
                        "filename": content.get("filename", content.get("title", "Unknown")),
                        "content_name": content.get("name", content.get("title", "Unknown")),
                        "content_type": content.get("content_type", "Unknown")
                    })
                else:
                    # If content not found in database, use event payload data
                    context.update({
                        "filename": event.payload.get("filename", event.payload.get("title", "Unknown")),
                        "content_name": event.payload.get("title", "Unknown"),
                        "content_type": event.payload.get("content_type", "Unknown")
                    })

            # Get device information
            if event.device_id:
                device = await db_service.get_document("devices", {"_id": event.device_id})
                if device:
                    context.update({
                        "device_name": device.get("name", "Unknown Device"),
                        "device_location": device.get("location", {}).get("name", "Unknown Location")
                    })

            # Get user information
            if event.user_id:
                user = await db_service.get_document("users", {"_id": event.user_id})
                if user:
                    context.update({
                        "user_name": user.get("name", "Unknown User"),
                        "user_email": user.get("email", "Unknown")
                    })

            # Add payload data
            if event.payload:
                # Rejection reason
                if "rejection_reason" in event.payload:
                    context["rejection_reason"] = event.payload["rejection_reason"]

                # Error message
                if "error_message" in event.payload:
                    context["error_message"] = event.payload["error_message"]

                # Device count
                if "device_count" in event.payload:
                    context["device_count"] = event.payload["device_count"]

                # New status
                if "new_status" in event.payload:
                    context["new_status"] = event.payload["new_status"]

        except Exception as e:
            logger.error(f"Failed to get context data for event {event.event_id}: {e}")

        return context

    async def _get_notification_recipients(self, company_id: str, recipient_roles: List[str], event: Event) -> List[str]:
        """Get user IDs for notification recipients based on roles"""
        try:
            recipients = set()

            for role in recipient_roles:
                if role == "content_reviewers":
                    # Get users with content review permissions
                    users = await db_service.find_documents("users", {
                        "company_id": company_id,
                        "is_active": True,
                        "$or": [
                            {"company_role": "REVIEWER"},
                            {"company_role": "ADMIN"},
                            {"permissions": {"$in": ["content_approve", "content_moderate"]}}
                        ]
                    })
                    recipients.update(user["_id"] for user in users)

                elif role == "content_editors":
                    # Get users with content editing permissions
                    users = await db_service.find_documents("users", {
                        "company_id": company_id,
                        "is_active": True,
                        "$or": [
                            {"company_role": "EDITOR"},
                            {"company_role": "ADMIN"},
                            {"permissions": {"$in": ["content_create", "content_update"]}}
                        ]
                    })
                    recipients.update(user["_id"] for user in users)

                elif role == "device_managers":
                    # Get users with device management permissions
                    users = await db_service.find_documents("users", {
                        "company_id": company_id,
                        "is_active": True,
                        "$or": [
                            {"company_role": "ADMIN"},
                            {"permissions": {"$in": ["device_manage", "device_update"]}}
                        ]
                    })
                    recipients.update(user["_id"] for user in users)

                elif role == "company_admins":
                    # Get company administrators
                    users = await db_service.find_documents("users", {
                        "company_id": company_id,
                        "company_role": "ADMIN",
                        "is_active": True
                    })
                    recipients.update(user["_id"] for user in users)

                elif role == "technical_support":
                    # Get super users for technical support
                    users = await db_service.find_documents("users", {
                        "user_type": "SUPER_USER",
                        "is_active": True
                    })
                    recipients.update(user["_id"] for user in users)

                elif role == "content_owner":
                    # Get the content owner
                    if event.user_id:
                        recipients.add(event.user_id)

            return list(recipients)

        except Exception as e:
            logger.error(f"Failed to get notification recipients: {e}")
            return []

    async def _store_notification(self, notification: Dict[str, Any]):
        """Store notification in database"""
        try:
            # Create individual notification records for each recipient
            notification_docs = []
            for recipient_id in notification["recipients"]:
                doc = {
                    **notification,
                    "recipient_id": recipient_id,
                    "read": False,
                    "read_at": None,
                    "delivered": False,
                    "delivered_at": None
                }
                # Remove the recipients list from individual notifications
                doc.pop("recipients", None)
                notification_docs.append(doc)

            # Batch insert notifications
            if notification_docs:
                await db_service.insert_many("notifications", notification_docs)
                logger.info(f"Stored {len(notification_docs)} notifications for event {notification['event_id']}")

        except Exception as e:
            logger.error(f"Failed to store notification: {e}")

    async def _send_real_time_notification(self, notification: Dict[str, Any]):
        """Send real-time notification via WebSocket (placeholder)"""
        try:
            # This would integrate with WebSocket service for real-time notifications
            # For now, just log the notification
            logger.info(f"Real-time notification: {notification['title']} to {len(notification['recipients'])} recipients")

            # In a real implementation, this would:
            # 1. Check if recipients are online
            # 2. Send WebSocket message to connected users
            # 3. Update delivery status

        except Exception as e:
            logger.error(f"Failed to send real-time notification: {e}")

    async def _handle_urgent_notification(self, notification: Dict[str, Any]):
        """Handle urgent notifications with additional processing"""
        try:
            logger.warning(f"URGENT NOTIFICATION: {notification['title']} - {notification['message']}")

            # For urgent notifications, you might want to:
            # 1. Send email notifications
            # 2. Send SMS alerts
            # 3. Create escalation tickets
            # 4. Log to monitoring systems

            # Mark as urgent in database
            await db_service.update_many(
                "notifications",
                {
                    "event_id": notification["event_id"],
                    "type": notification["type"]
                },
                {
                    "$set": {
                        "urgent": True,
                        "escalated": True,
                        "escalated_at": datetime.utcnow()
                    }
                }
            )

        except Exception as e:
            logger.error(f"Failed to handle urgent notification: {e}")

    async def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read by user"""
        try:
            result = await db_service.update_document(
                "notifications",
                {
                    "id": notification_id,
                    "recipient_id": user_id,
                    "read": False
                },
                {
                    "$set": {
                        "read": True,
                        "read_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False

    async def get_user_notifications(self, user_id: str, company_id: str,
                                   limit: int = 50, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        try:
            query = {
                "recipient_id": user_id,
                "company_id": company_id
            }

            if unread_only:
                query["read"] = False

            notifications = await db_service.find_documents(
                "notifications",
                query,
                sort=[("created_at", -1)],
                limit=limit
            )

            return notifications

        except Exception as e:
            logger.error(f"Failed to get user notifications: {e}")
            return []