"""
Content History and Audit Tracking Service
Provides comprehensive tracking of content lifecycle events, device activities, and system audit logs.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from fastapi import HTTPException, Request
import logging
from app.models import (
    ContentHistory, ContentHistoryEventType, ContentHistoryQuery,
    ContentLifecycleSummary, ContentAuditReport, HistoryEventCreate,
    ContentTimelineView, DeviceHistory, DeviceHistoryEventType,
    SystemAuditLog, ContentMeta, User
)
from app.database_service import DatabaseService

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for tracking and querying content and system history"""

    def __init__(self, db_service: DatabaseService):
        self.db = db_service

    async def track_content_event(
        self,
        content_id: str,
        event_type: ContentHistoryEventType,
        company_id: str,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None,
        event_details: Optional[Dict] = None,
        previous_state: Optional[Dict] = None,
        new_state: Optional[Dict] = None,
        triggered_by_system: Optional[str] = None,
        error_info: Optional[Dict] = None,
        request: Optional[Request] = None,
        processing_time_ms: Optional[int] = None
    ) -> str:
        """
        Track a content lifecycle event

        Args:
            content_id: ID of the content
            event_type: Type of event (uploaded, approved, etc.)
            company_id: Company context
            user_id: User who triggered the event (if applicable)
            device_id: Device involved (if applicable)
            event_details: Additional event-specific data
            previous_state: State before the event
            new_state: State after the event
            triggered_by_system: System component that triggered the event
            error_info: Error details if applicable
            request: FastAPI request for extracting metadata
            processing_time_ms: Time taken to process the event

        Returns:
            History event ID
        """
        try:
            # Get user information if user_id is provided
            user_name = None
            user_type = None
            if user_id:
                try:
                    user = await self.db.get_user_by_id(user_id)
                    if user:
                        user_name = user.get("name") or user.get("email")
                        user_type = user.get("user_type")
                except Exception as e:
                    logger.warning(f"Could not fetch user info for {user_id}: {e}")

            # Extract request metadata
            ip_address = None
            user_agent = None
            session_id = None

            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                session_id = request.headers.get("x-session-id")

            # Create history event
            history_event = ContentHistory(
                content_id=content_id,
                event_type=event_type,
                triggered_by_user_id=user_id,
                triggered_by_user_name=user_name,
                triggered_by_user_type=user_type,
                triggered_by_system=triggered_by_system,
                device_id=device_id,
                company_id=company_id,
                event_details=event_details or {},
                previous_state=previous_state,
                new_state=new_state,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                processing_time_ms=processing_time_ms
            )

            # Add error information if provided
            if error_info:
                history_event.error_code = error_info.get("code")
                history_event.error_message = error_info.get("message")
                history_event.stack_trace = error_info.get("stack_trace")

            # Save to database
            result = await self.db.create_content_history(history_event.model_dump(exclude_none=True))

            logger.info(f"Tracked content event: {event_type} for content {content_id}")
            return result.get("id", "")

        except Exception as e:
            logger.error(f"Failed to track content event: {e}")
            # Don't let history tracking failures break the main flow
            return ""

    async def track_device_event(
        self,
        device_id: str,
        event_type: DeviceHistoryEventType,
        company_id: str,
        content_id: Optional[str] = None,
        user_id: Optional[str] = None,
        event_data: Optional[Dict] = None,
        system_metrics: Optional[Dict] = None,
        error_info: Optional[Dict] = None
    ) -> str:
        """Track a device-related event"""
        try:
            device_event = DeviceHistory(
                device_id=device_id,
                event_type=event_type,
                content_id=content_id,
                company_id=company_id,
                triggered_by_user_id=user_id,
                event_data=event_data or {},
                system_metrics=system_metrics,
                error_code=error_info.get("code") if error_info else None,
                error_message=error_info.get("message") if error_info else None
            )

            result = await self.db.create_device_history(device_event.model_dump(exclude_none=True))

            logger.info(f"Tracked device event: {event_type} for device {device_id}")
            return result.get("id", "")

        except Exception as e:
            logger.error(f"Failed to track device event: {e}")
            return ""

    async def get_content_history(
        self,
        query: ContentHistoryQuery,
        user_company_id: str
    ) -> List[ContentHistory]:
        """Get content history with filtering"""
        try:
            # Build query filters
            filters = {"company_id": user_company_id}

            if query.content_ids:
                filters["content_id"] = {"$in": query.content_ids}

            if query.event_types:
                filters["event_type"] = {"$in": [et.value for et in query.event_types]}

            if query.user_ids:
                filters["triggered_by_user_id"] = {"$in": query.user_ids}

            if query.device_ids:
                filters["device_id"] = {"$in": query.device_ids}

            if query.start_date or query.end_date:
                date_filter = {}
                if query.start_date:
                    date_filter["$gte"] = query.start_date
                if query.end_date:
                    date_filter["$lte"] = query.end_date
                filters["event_timestamp"] = date_filter

            if not query.include_system_events:
                filters["triggered_by_system"] = {"$exists": False}

            if not query.include_error_events:
                filters["error_code"] = {"$exists": False}

            # Execute query
            sort_order = -1 if query.sort_order == "desc" else 1

            results = await self.db.find_content_history(
                filters=filters,
                limit=query.limit,
                offset=query.offset,
                sort=[("event_timestamp", sort_order)]
            )

            return [ContentHistory(**result) for result in results]

        except Exception as e:
            logger.error(f"Failed to get content history: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve content history")

    async def get_content_timeline(
        self,
        content_id: str,
        company_id: str
    ) -> ContentTimelineView:
        """Get timeline view for a specific content item"""
        try:
            # Get content information
            content = await self.db.get_content_by_id(content_id, company_id)
            if not content:
                raise HTTPException(status_code=404, detail="Content not found")

            # Get all history events for this content
            history_events = await self.db.find_content_history(
                filters={"content_id": content_id, "company_id": company_id},
                sort=[("event_timestamp", 1)]
            )

            # Process timeline events
            timeline_events = []
            milestones = []

            for event in history_events:
                timeline_event = {
                    "id": event["id"],
                    "type": event["event_type"],
                    "timestamp": event["event_timestamp"],
                    "user": event.get("triggered_by_user_name"),
                    "system": event.get("triggered_by_system"),
                    "details": event.get("event_details", {}),
                    "success": not event.get("error_code"),
                    "processing_time": event.get("processing_time_ms")
                }
                timeline_events.append(timeline_event)

                # Mark milestones
                if event["event_type"] in ["uploaded", "approved", "deployed", "displayed"]:
                    milestones.append({
                        "type": event["event_type"],
                        "timestamp": event["event_timestamp"],
                        "completed": True
                    })

            # Determine current phase
            current_phase = self._determine_content_phase(content, timeline_events)

            # Calculate performance score
            performance_score = self._calculate_performance_score(timeline_events)

            # Identify bottlenecks
            bottlenecks = self._identify_bottlenecks(timeline_events)

            return ContentTimelineView(
                content_id=content_id,
                content_title=content.get("title", "Untitled"),
                timeline_events=timeline_events,
                milestones=milestones,
                current_phase=current_phase,
                performance_score=performance_score,
                bottlenecks=bottlenecks
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get content timeline: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve content timeline")

    async def get_content_lifecycle_summary(
        self,
        content_id: str,
        company_id: str
    ) -> ContentLifecycleSummary:
        """Get comprehensive lifecycle summary for content"""
        try:
            # Get content information
            content = await self.db.get_content_by_id(content_id, company_id)
            if not content:
                raise HTTPException(status_code=404, detail="Content not found")

            # Get history events
            history_events = await self.db.find_content_history(
                filters={"content_id": content_id, "company_id": company_id}
            )

            # Extract key timestamps
            uploaded_at = None
            ai_moderation_completed_at = None
            approved_at = None
            first_deployed_at = None
            last_displayed_at = None

            uploaded_by = None
            reviewed_by = None
            last_modified_by = None

            total_deployments = 0
            total_displays = 0
            total_errors = 0
            processing_times = []

            for event in history_events:
                event_type = event["event_type"]
                timestamp = event["event_timestamp"]

                if event_type == "uploaded" and not uploaded_at:
                    uploaded_at = timestamp
                    uploaded_by = event.get("triggered_by_user_name")

                elif event_type == "ai_moderation_completed" and not ai_moderation_completed_at:
                    ai_moderation_completed_at = timestamp

                elif event_type == "approved" and not approved_at:
                    approved_at = timestamp
                    reviewed_by = event.get("triggered_by_user_name")

                elif event_type == "deployed":
                    if not first_deployed_at:
                        first_deployed_at = timestamp
                    total_deployments += 1

                elif event_type == "displayed":
                    last_displayed_at = timestamp
                    total_displays += 1

                if event.get("error_code"):
                    total_errors += 1

                if event.get("processing_time_ms"):
                    processing_times.append(event["processing_time_ms"])

                if event.get("triggered_by_user_name"):
                    last_modified_by = event["triggered_by_user_name"]

            # Calculate metrics
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else None

            # Get recent events (last 10)
            recent_events = sorted(
                history_events,
                key=lambda x: x["event_timestamp"],
                reverse=True
            )[:10]

            recent_events_formatted = [
                {
                    "type": event["event_type"],
                    "timestamp": event["event_timestamp"],
                    "user": event.get("triggered_by_user_name"),
                    "success": not event.get("error_code")
                }
                for event in recent_events
            ]

            last_activity_at = recent_events[0]["event_timestamp"] if recent_events else None

            return ContentLifecycleSummary(
                content_id=content_id,
                content_title=content.get("title", "Untitled"),
                current_status=content.get("status", "unknown"),
                company_id=company_id,
                company_name="",  # TODO: Get company name
                uploaded_at=uploaded_at,
                ai_moderation_completed_at=ai_moderation_completed_at,
                approved_at=approved_at,
                first_deployed_at=first_deployed_at,
                last_displayed_at=last_displayed_at,
                total_deployments=total_deployments,
                total_displays=total_displays,
                total_errors=total_errors,
                avg_processing_time_ms=avg_processing_time,
                uploaded_by=uploaded_by,
                reviewed_by=reviewed_by,
                last_modified_by=last_modified_by,
                recent_events=recent_events_formatted,
                last_activity_at=last_activity_at
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get content lifecycle summary: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve lifecycle summary")

    async def generate_audit_report(
        self,
        company_id: str,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "custom",
        generated_by: str = ""
    ) -> ContentAuditReport:
        """Generate comprehensive audit report"""
        try:
            # Get all content history events in the date range
            filters = {
                "company_id": company_id,
                "event_timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            history_events = await self.db.find_content_history(filters=filters)

            # Calculate statistics
            events_by_type = {}
            events_by_user_type = {}
            uploaded_count = 0
            approved_count = 0
            rejected_count = 0
            deployed_count = 0
            error_count = 0

            processing_times = []
            approval_times = []
            deployment_times = []

            uploader_activity = {}
            reviewer_activity = {}

            for event in history_events:
                event_type = event["event_type"]
                events_by_type[event_type] = events_by_type.get(event_type, 0) + 1

                user_type = event.get("triggered_by_user_type", "system")
                events_by_user_type[user_type] = events_by_user_type.get(user_type, 0) + 1

                if event_type == "uploaded":
                    uploaded_count += 1
                    user_name = event.get("triggered_by_user_name", "Unknown")
                    uploader_activity[user_name] = uploader_activity.get(user_name, 0) + 1

                elif event_type == "approved":
                    approved_count += 1
                    user_name = event.get("triggered_by_user_name", "Unknown")
                    reviewer_activity[user_name] = reviewer_activity.get(user_name, 0) + 1

                elif event_type == "rejected":
                    rejected_count += 1

                elif event_type == "deployed":
                    deployed_count += 1

                if event.get("error_code"):
                    error_count += 1

                if event.get("processing_time_ms"):
                    processing_times.append(event["processing_time_ms"])

            # Calculate averages
            avg_approval_time = None
            avg_deployment_time = None
            success_rate = None
            error_rate = None

            if history_events:
                total_events = len(history_events)
                success_rate = ((total_events - error_count) / total_events) * 100
                error_rate = (error_count / total_events) * 100

            # Format top performers
            most_active_uploaders = [
                {"name": name, "count": count}
                for name, count in sorted(uploader_activity.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

            most_active_reviewers = [
                {"name": name, "count": count}
                for name, count in sorted(reviewer_activity.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

            return ContentAuditReport(
                company_id=company_id,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                generated_by=generated_by,
                total_content_uploaded=uploaded_count,
                total_content_approved=approved_count,
                total_content_rejected=rejected_count,
                total_content_deployed=deployed_count,
                avg_approval_time_hours=avg_approval_time,
                avg_deployment_time_hours=avg_deployment_time,
                success_rate_percentage=success_rate,
                most_active_uploaders=most_active_uploaders,
                most_active_reviewers=most_active_reviewers,
                error_rate_percentage=error_rate,
                events_by_type=events_by_type,
                events_by_user_type=events_by_user_type
            )

        except Exception as e:
            logger.error(f"Failed to generate audit report: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate audit report")

    def _determine_content_phase(self, content: Dict, timeline_events: List[Dict]) -> str:
        """Determine current phase of content lifecycle"""
        status = content.get("status", "unknown")

        # Map database status to UI phase
        status_mapping = {
            "quarantine": "upload",
            "pending": "moderation",
            "approved": "approved",
            "rejected": "rejected",
            "active": "deployed"
        }

        return status_mapping.get(status, "unknown")

    def _calculate_performance_score(self, timeline_events: List[Dict]) -> Optional[float]:
        """Calculate performance score based on processing times and success rate"""
        if not timeline_events:
            return None

        try:
            total_events = len(timeline_events)
            successful_events = sum(1 for event in timeline_events if event.get("success", True))

            success_rate = successful_events / total_events

            # Factor in processing times
            processing_times = [
                event.get("processing_time", 0)
                for event in timeline_events
                if event.get("processing_time")
            ]

            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

            # Score: 70% success rate + 30% speed (inverse of processing time)
            speed_score = max(0, 1 - (avg_processing_time / 10000))  # Normalize to 10 seconds
            performance_score = (success_rate * 0.7) + (speed_score * 0.3)

            return round(performance_score * 100, 2)

        except Exception:
            return None

    def _identify_bottlenecks(self, timeline_events: List[Dict]) -> List[Dict]:
        """Identify potential bottlenecks in the content lifecycle"""
        bottlenecks = []

        try:
            # Check for long gaps between events
            for i in range(1, len(timeline_events)):
                prev_event = timeline_events[i - 1]
                curr_event = timeline_events[i]

                time_diff = (curr_event["timestamp"] - prev_event["timestamp"]).total_seconds() / 3600  # hours

                if time_diff > 24:  # More than 24 hours
                    bottlenecks.append({
                        "type": "long_gap",
                        "phase": f"{prev_event['type']} -> {curr_event['type']}",
                        "duration_hours": round(time_diff, 2),
                        "severity": "high" if time_diff > 72 else "medium"
                    })

            # Check for high error rates
            error_events = [event for event in timeline_events if not event.get("success", True)]
            if len(error_events) / len(timeline_events) > 0.2:  # More than 20% errors
                bottlenecks.append({
                    "type": "high_error_rate",
                    "error_count": len(error_events),
                    "total_events": len(timeline_events),
                    "severity": "high"
                })

        except Exception as e:
            logger.warning(f"Failed to identify bottlenecks: {e}")

        return bottlenecks

    async def track_system_audit(
        self,
        audit_type: str,
        resource_type: str,
        resource_id: str,
        action_performed: str,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        request_data: Optional[Dict] = None,
        response_data: Optional[Dict] = None,
        success: bool = True,
        error_info: Optional[Dict] = None,
        request: Optional[Request] = None
    ) -> str:
        """Track system-wide audit events for compliance"""
        try:
            audit_log = SystemAuditLog(
                audit_type=audit_type,
                resource_type=resource_type,
                resource_id=resource_id,
                action_performed=action_performed,
                performed_by_user_id=user_id,
                company_id=company_id,
                request_data=request_data,
                response_data=response_data,
                success=success
            )

            if request:
                audit_log.ip_address = request.client.host if request.client else None
                audit_log.user_agent = request.headers.get("user-agent")
                audit_log.session_id = request.headers.get("x-session-id")

            if error_info:
                audit_log.error_code = error_info.get("code")
                audit_log.error_message = error_info.get("message")

            result = await self.db.create_system_audit_log(audit_log.model_dump(exclude_none=True))

            return result.get("id", "")

        except Exception as e:
            logger.error(f"Failed to track system audit: {e}")
            return ""