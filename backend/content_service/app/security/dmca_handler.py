"""
DMCA Compliance Handler
Implements Digital Millennium Copyright Act (DMCA) compliance including:
- Takedown request processing
- Counter-notice handling
- Safe harbor provisions
- Copyright holder verification
- Legal documentation generation
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .config_manager import config_manager
from .audit_logger import audit_logger, AuditSeverity

logger = logging.getLogger(__name__)

class DMCARequestType(Enum):
    TAKEDOWN = "takedown"
    COUNTER_NOTICE = "counter_notice"

class DMCARequestStatus(Enum):
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    VALID = "valid"
    INVALID = "invalid"
    PROCESSED = "processed"
    REJECTED = "rejected"
    COUNTER_CLAIMED = "counter_claimed"

class DMCATakedownRequest:
    """DMCA Takedown Request Data Structure"""
    def __init__(self, request_data: Dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc)
        self.type = DMCARequestType.TAKEDOWN
        self.status = DMCARequestStatus.RECEIVED
        
        # Copyright holder information
        self.copyright_holder_name = request_data.get('copyright_holder_name', '')
        self.copyright_holder_email = request_data.get('copyright_holder_email', '')
        self.copyright_holder_address = request_data.get('copyright_holder_address', '')
        self.copyright_holder_phone = request_data.get('copyright_holder_phone', '')
        
        # Representative information (if applicable)
        self.representative_name = request_data.get('representative_name')
        self.representative_email = request_data.get('representative_email')
        
        # Copyrighted work information
        self.work_title = request_data.get('work_title', '')
        self.work_description = request_data.get('work_description', '')
        self.original_work_location = request_data.get('original_work_location', '')
        self.copyright_registration = request_data.get('copyright_registration')
        
        # Infringing content information
        self.infringing_content_urls = request_data.get('infringing_content_urls', [])
        self.infringing_content_ids = request_data.get('infringing_content_ids', [])
        self.infringement_description = request_data.get('infringement_description', '')
        
        # Legal statements
        self.good_faith_statement = request_data.get('good_faith_statement', False)
        self.perjury_statement = request_data.get('perjury_statement', False)
        self.electronic_signature = request_data.get('electronic_signature', '')
        
        # Processing information
        self.processed_at = None
        self.processing_notes = []
        self.counter_notice_deadline = None

class DMCACounterNotice:
    """DMCA Counter Notice Data Structure"""
    def __init__(self, request_data: Dict[str, Any], original_takedown_id: str):
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc)
        self.type = DMCARequestType.COUNTER_NOTICE
        self.status = DMCARequestStatus.RECEIVED
        self.original_takedown_id = original_takedown_id
        
        # User information
        self.user_name = request_data.get('user_name', '')
        self.user_email = request_data.get('user_email', '')
        self.user_address = request_data.get('user_address', '')
        self.user_phone = request_data.get('user_phone', '')
        
        # Content information
        self.content_ids = request_data.get('content_ids', [])
        self.content_description = request_data.get('content_description', '')
        
        # Legal statements
        self.good_faith_statement = request_data.get('good_faith_statement', False)
        self.perjury_statement = request_data.get('perjury_statement', False)
        self.jurisdiction_consent = request_data.get('jurisdiction_consent', False)
        self.electronic_signature = request_data.get('electronic_signature', '')
        
        # Counter notice explanation
        self.counter_explanation = request_data.get('counter_explanation', '')
        
        # Processing information
        self.processed_at = None
        self.processing_notes = []
        self.restore_deadline = None

class DMCAComplianceHandler:
    """Handles DMCA takedown requests and counter notices"""
    
    def __init__(self):
        self.compliance_config = config_manager.get_compliance_config()
        self.dmca_email = self.compliance_config.get('dmca_email', 'dmca@localhost')
        
        # DMCA processing timelines (per US law)
        self.takedown_processing_days = 1  # Must act expeditiously
        self.counter_notice_period_days = 10  # Copyright holder has 10-14 days to file suit
        self.restore_period_days = 14  # Content restored after 10-14 days if no suit filed
        
        # Storage (in production, use database)
        self.takedown_requests = {}
        self.counter_notices = {}
        
    async def process_takedown_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a DMCA takedown request"""
        try:
            # Create takedown request object
            request = DMCATakedownRequest(request_data)
            
            # Validate request
            validation_result = self._validate_takedown_request(request)
            if not validation_result['valid']:
                request.status = DMCARequestStatus.INVALID
                self.takedown_requests[request.id] = request
                
                # Log invalid request
                audit_logger.log_content_event("dmca_takedown_invalid", request.id, {
                    "copyright_holder": request.copyright_holder_email,
                    "validation_errors": validation_result['errors']
                })
                
                return {
                    "success": False,
                    "request_id": request.id,
                    "status": request.status.value,
                    "errors": validation_result['errors']
                }
            
            # Store request
            request.status = DMCARequestStatus.UNDER_REVIEW
            self.takedown_requests[request.id] = request
            
            # Send acknowledgment email
            await self._send_takedown_acknowledgment(request)
            
            # Process takedown (remove/disable content)
            processed_content = await self._process_content_takedown(request)
            
            if processed_content['success']:
                request.status = DMCARequestStatus.PROCESSED
                request.processed_at = datetime.now(timezone.utc)
                request.counter_notice_deadline = request.processed_at + timedelta(days=self.counter_notice_period_days)
                
                # Notify content uploader about takedown
                await self._notify_content_uploader(request, processed_content['affected_content'])\n                
                # Log successful takedown
                audit_logger.log_content_event("dmca_takedown_processed", request.id, {
                    "copyright_holder": request.copyright_holder_email,
                    "affected_content_count": len(processed_content['affected_content']),
                    "processing_time_minutes": (datetime.now(timezone.utc) - request.timestamp).total_seconds() / 60
                })
                
                return {
                    "success": True,
                    "request_id": request.id,
                    "status": request.status.value,
                    "affected_content": processed_content['affected_content'],
                    "counter_notice_deadline": request.counter_notice_deadline.isoformat()
                }
            else:
                request.status = DMCARequestStatus.REJECTED
                request.processing_notes.append(f"Failed to process content: {processed_content.get('error', 'Unknown error')}")
                
                return {
                    "success": False,
                    "request_id": request.id,
                    "status": request.status.value,
                    "error": processed_content.get('error', 'Failed to process takedown')
                }
                
        except Exception as e:
            logger.error(f"DMCA takedown processing failed: {e}")
            audit_logger.log_security_event("dmca_processing_error", {
                "error": str(e),
                "request_type": "takedown"
            }, severity=AuditSeverity.HIGH)
            
            return {
                "success": False,
                "error": "Internal processing error"
            }
    
    async def process_counter_notice(self, request_data: Dict[str, Any], 
                                   takedown_request_id: str) -> Dict[str, Any]:
        """Process a DMCA counter notice"""
        try:
            # Verify original takedown exists
            if takedown_request_id not in self.takedown_requests:
                return {
                    "success": False,
                    "error": "Original takedown request not found"
                }
            
            original_takedown = self.takedown_requests[takedown_request_id]
            if original_takedown.status != DMCARequestStatus.PROCESSED:
                return {
                    "success": False,
                    "error": "Original takedown request not in valid state for counter notice"
                }
            
            # Create counter notice object
            counter_notice = DMCACounterNotice(request_data, takedown_request_id)
            
            # Validate counter notice
            validation_result = self._validate_counter_notice(counter_notice)
            if not validation_result['valid']:
                counter_notice.status = DMCARequestStatus.INVALID
                self.counter_notices[counter_notice.id] = counter_notice
                
                return {
                    "success": False,
                    "counter_notice_id": counter_notice.id,
                    "status": counter_notice.status.value,
                    "errors": validation_result['errors']
                }
            
            # Store counter notice
            counter_notice.status = DMCARequestStatus.UNDER_REVIEW
            counter_notice.restore_deadline = datetime.now(timezone.utc) + timedelta(days=self.restore_period_days)
            self.counter_notices[counter_notice.id] = counter_notice
            
            # Update original takedown status
            original_takedown.status = DMCARequestStatus.COUNTER_CLAIMED
            
            # Send acknowledgment to counter-notifier
            await self._send_counter_notice_acknowledgment(counter_notice)
            
            # Notify original copyright holder
            await self._notify_copyright_holder_of_counter_notice(original_takedown, counter_notice)
            
            # Log counter notice
            audit_logger.log_content_event("dmca_counter_notice_received", counter_notice.id, {
                "original_takedown_id": takedown_request_id,
                "user_email": counter_notice.user_email,
                "restore_deadline": counter_notice.restore_deadline.isoformat()
            })
            
            return {
                "success": True,
                "counter_notice_id": counter_notice.id,
                "status": counter_notice.status.value,
                "restore_deadline": counter_notice.restore_deadline.isoformat(),
                "message": "Counter notice received. Content will be restored in 10-14 days unless copyright holder files suit."
            }
            
        except Exception as e:
            logger.error(f"DMCA counter notice processing failed: {e}")
            audit_logger.log_security_event("dmca_processing_error", {
                "error": str(e),
                "request_type": "counter_notice"
            }, severity=AuditSeverity.HIGH)
            
            return {
                "success": False,
                "error": "Internal processing error"
            }
    
    def _validate_takedown_request(self, request: DMCATakedownRequest) -> Dict[str, Any]:
        """Validate DMCA takedown request completeness"""
        errors = []
        
        # Required copyright holder information
        if not request.copyright_holder_name:
            errors.append("Copyright holder name is required")
        if not request.copyright_holder_email:
            errors.append("Copyright holder email is required")
        if not request.copyright_holder_address:
            errors.append("Copyright holder address is required")
        
        # Required work information
        if not request.work_title and not request.work_description:
            errors.append("Work title or description is required")
        
        # Required infringement information
        if not request.infringing_content_urls and not request.infringing_content_ids:
            errors.append("Infringing content URLs or IDs are required")
        if not request.infringement_description:
            errors.append("Description of infringement is required")
        
        # Required legal statements
        if not request.good_faith_statement:
            errors.append("Good faith statement is required")
        if not request.perjury_statement:
            errors.append("Perjury statement is required")
        if not request.electronic_signature:
            errors.append("Electronic signature is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_counter_notice(self, notice: DMCACounterNotice) -> Dict[str, Any]:
        """Validate DMCA counter notice completeness"""
        errors = []
        
        # Required user information
        if not notice.user_name:
            errors.append("User name is required")
        if not notice.user_email:
            errors.append("User email is required")
        if not notice.user_address:
            errors.append("User address is required")
        
        # Required content information
        if not notice.content_ids:
            errors.append("Content IDs are required")
        if not notice.content_description:
            errors.append("Content description is required")
        
        # Required legal statements
        if not notice.good_faith_statement:
            errors.append("Good faith statement is required")
        if not notice.perjury_statement:
            errors.append("Perjury statement is required")
        if not notice.jurisdiction_consent:
            errors.append("Jurisdiction consent is required")
        if not notice.electronic_signature:
            errors.append("Electronic signature is required")
        if not notice.counter_explanation:
            errors.append("Counter explanation is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _process_content_takedown(self, request: DMCATakedownRequest) -> Dict[str, Any]:
        """Remove or disable infringing content"""
        try:
            affected_content = []
            
            # Process content IDs
            for content_id in request.infringing_content_ids:
                try:
                    # TODO: Implement content removal/disabling
                    # This should:
                    # 1. Mark content as DMCA_REMOVED
                    # 2. Stop distribution to devices
                    # 3. Archive original content
                    # 4. Update content status in database
                    
                    affected_content.append({
                        "content_id": content_id,
                        "action": "removed",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to remove content {content_id}: {e}")
            
            # Process content URLs (if any direct URLs provided)
            for url in request.infringing_content_urls:
                # Extract content ID from URL if possible
                # This depends on your URL structure
                pass
            
            return {
                "success": True,
                "affected_content": affected_content
            }
            
        except Exception as e:
            logger.error(f"Content takedown processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_takedown_acknowledgment(self, request: DMCATakedownRequest):
        """Send acknowledgment email to copyright holder"""
        try:
            subject = f"DMCA Takedown Request Received - Reference: {request.id}"
            
            body = f\"\"\"
Dear {request.copyright_holder_name},

Thank you for your DMCA takedown request. We have received your notice and are processing it in accordance with the Digital Millennium Copyright Act.

Request Details:
- Reference ID: {request.id}
- Received: {request.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
- Work Title: {request.work_title}
- Status: {request.status.value}

We will review your request and take appropriate action within 24 hours. You will receive another email once the request has been processed.

If you have any questions, please contact us at {self.dmca_email}.

Best regards,
Adara Digital Signage DMCA Team
\"\"\"
            
            await self._send_email(request.copyright_holder_email, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send takedown acknowledgment: {e}")
    
    async def _send_counter_notice_acknowledgment(self, notice: DMCACounterNotice):
        """Send acknowledgment email to counter-notice sender"""
        try:
            subject = f"DMCA Counter Notice Received - Reference: {notice.id}"
            
            body = f\"\"\"
Dear {notice.user_name},

We have received your DMCA counter notice regarding content that was previously removed due to a copyright complaint.

Counter Notice Details:
- Reference ID: {notice.id}
- Received: {notice.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
- Original Takedown ID: {notice.original_takedown_id}
- Status: {notice.status.value}

Per DMCA requirements, we have forwarded your counter notice to the original copyright holder. If they do not file a court order within 10-14 business days, we will restore your content.

Expected Restore Date: {notice.restore_deadline.strftime('%Y-%m-%d') if notice.restore_deadline else 'TBD'}

Best regards,
Adara Digital Signage DMCA Team
\"\"\"
            
            await self._send_email(notice.user_email, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send counter notice acknowledgment: {e}")
    
    async def _notify_content_uploader(self, request: DMCATakedownRequest, affected_content: List[Dict]):
        """Notify content uploader about takedown"""
        try:
            # TODO: Get uploader email from content metadata
            # For now, this is a placeholder
            
            for content in affected_content:
                content_id = content['content_id']
                # Get content details and uploader info
                # Send notification email
                pass
                
        except Exception as e:
            logger.error(f"Failed to notify content uploader: {e}")
    
    async def _notify_copyright_holder_of_counter_notice(self, takedown: DMCATakedownRequest, 
                                                        counter_notice: DMCACounterNotice):
        """Notify copyright holder of received counter notice"""
        try:
            subject = f"DMCA Counter Notice Received - Your Request: {takedown.id}"
            
            body = f\"\"\"
Dear {takedown.copyright_holder_name},

We have received a counter notice regarding your DMCA takedown request.

Original Request: {takedown.id}
Counter Notice: {counter_notice.id}
Counter Notice Date: {counter_notice.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Counter Notice Details:
User: {counter_notice.user_name}
User Email: {counter_notice.user_email}
Explanation: {counter_notice.counter_explanation}

Per DMCA Section 512(g), we will restore the content in 10-14 business days unless you file a court order to prevent restoration.

If you believe the counter notice is invalid or wish to prevent restoration, you must:
1. File a lawsuit against the user within 10-14 business days
2. Provide us with a copy of the filed court order

Restoration Date: {counter_notice.restore_deadline.strftime('%Y-%m-%d') if counter_notice.restore_deadline else 'TBD'}

Best regards,
Adara Digital Signage DMCA Team
\"\"\"
            
            await self._send_email(takedown.copyright_holder_email, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to notify copyright holder of counter notice: {e}")
    
    async def _send_email(self, to_email: str, subject: str, body: str):
        """Send email notification (placeholder implementation)"""
        try:
            # TODO: Implement actual email sending
            # This should use your configured SMTP server
            logger.info(f"DMCA Email to {to_email}: {subject}")
            logger.debug(f"Email body: {body}")
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
    
    async def process_expired_requests(self):
        """Process expired counter notices and restore content"""
        try:
            current_time = datetime.now(timezone.utc)
            
            for notice in self.counter_notices.values():
                if (notice.status == DMCARequestStatus.UNDER_REVIEW and 
                    notice.restore_deadline and 
                    current_time >= notice.restore_deadline):
                    
                    # Restore content
                    await self._restore_content(notice)
                    
                    # Update status
                    notice.status = DMCARequestStatus.PROCESSED
                    notice.processed_at = current_time
                    
                    # Log restoration
                    audit_logger.log_content_event("dmca_content_restored", notice.id, {
                        "original_takedown_id": notice.original_takedown_id,
                        "restore_reason": "counter_notice_period_expired"
                    })
                    
        except Exception as e:
            logger.error(f"Processing expired DMCA requests failed: {e}")
    
    async def _restore_content(self, counter_notice: DMCACounterNotice):
        """Restore content after successful counter notice"""
        try:
            for content_id in counter_notice.content_ids:
                # TODO: Implement content restoration
                # This should:
                # 1. Reactivate content
                # 2. Resume distribution to devices
                # 3. Update content status in database
                pass
                
        except Exception as e:
            logger.error(f"Content restoration failed: {e}")
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of DMCA request"""
        if request_id in self.takedown_requests:
            request = self.takedown_requests[request_id]
            return {
                "id": request.id,
                "type": request.type.value,
                "status": request.status.value,
                "timestamp": request.timestamp.isoformat(),
                "processed_at": request.processed_at.isoformat() if request.processed_at else None
            }
        elif request_id in self.counter_notices:
            notice = self.counter_notices[request_id]
            return {
                "id": notice.id,
                "type": notice.type.value,
                "status": notice.status.value,
                "timestamp": notice.timestamp.isoformat(),
                "restore_deadline": notice.restore_deadline.isoformat() if notice.restore_deadline else None
            }
        return None

# Global DMCA handler instance
dmca_handler = DMCAComplianceHandler()