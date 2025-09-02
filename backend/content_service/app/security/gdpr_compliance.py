"""
GDPR Compliance Manager
Implements General Data Protection Regulation compliance including:
- Data subject rights (access, rectification, erasure, portability)
- Consent management
- Data retention policies
- Privacy by design
- Breach notification
- Data processing records
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import uuid

from .config_manager import config_manager
from .audit_logger import audit_logger, AuditSeverity

logger = logging.getLogger(__name__)

class DataSubjectRights(Enum):
    """GDPR Article 12-22: Rights of the data subject"""
    ACCESS = "access"  # Article 15
    RECTIFICATION = "rectification"  # Article 16
    ERASURE = "erasure"  # Article 17 (Right to be forgotten)
    RESTRICTION = "restriction"  # Article 18
    PORTABILITY = "portability"  # Article 20
    OBJECTION = "objection"  # Article 21

class ConsentStatus(Enum):
    """Consent status tracking"""
    GIVEN = "given"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"
    EXPIRED = "expired"

class DataCategory(Enum):
    """Categories of personal data"""
    IDENTITY = "identity"  # Name, email, phone
    CONTACT = "contact"  # Address, phone, email
    TECHNICAL = "technical"  # IP, device info, browser
    BEHAVIORAL = "behavioral"  # Usage patterns, preferences
    CONTENT = "content"  # User-generated content
    FINANCIAL = "financial"  # Payment info (handled separately)
    BIOMETRIC = "biometric"  # Biometric identifiers
    LOCATION = "location"  # Location data

class ProcessingPurpose(Enum):
    """Lawful purposes for data processing"""
    CONTRACT = "contract"  # Article 6(1)(b)
    LEGAL_OBLIGATION = "legal_obligation"  # Article 6(1)(c)
    VITAL_INTERESTS = "vital_interests"  # Article 6(1)(d)
    PUBLIC_TASK = "public_task"  # Article 6(1)(e)
    LEGITIMATE_INTEREST = "legitimate_interest"  # Article 6(1)(f)
    CONSENT = "consent"  # Article 6(1)(a)

class GDPRRequest:
    """GDPR data subject request"""
    def __init__(self, subject_id: str, request_type: DataSubjectRights, 
                 details: Dict[str, Any] = None):
        self.id = str(uuid.uuid4())
        self.subject_id = subject_id
        self.request_type = request_type
        self.status = "received"
        self.created_at = datetime.now(timezone.utc)
        self.details = details or {}
        self.processed_at = None
        self.response_data = None
        self.verification_token = None

class ConsentRecord:
    """User consent tracking"""
    def __init__(self, subject_id: str, purpose: ProcessingPurpose, 
                 data_categories: List[DataCategory]):
        self.id = str(uuid.uuid4())
        self.subject_id = subject_id
        self.purpose = purpose
        self.data_categories = data_categories
        self.status = ConsentStatus.GIVEN
        self.given_at = datetime.now(timezone.utc)
        self.withdrawn_at = None
        self.expires_at = None
        self.legal_basis = "consent"
        self.consent_text = ""
        self.version = "1.0"

class DataProcessingRecord:
    """Article 30: Records of processing activities"""
    def __init__(self, purpose: ProcessingPurpose, data_categories: List[DataCategory],
                 legal_basis: str, retention_period: int):
        self.id = str(uuid.uuid4())
        self.purpose = purpose
        self.data_categories = data_categories
        self.legal_basis = legal_basis
        self.retention_period_days = retention_period
        self.created_at = datetime.now(timezone.utc)
        self.data_subjects = set()  # Set of subject IDs
        self.processors = []  # List of data processors
        self.recipients = []  # List of data recipients
        self.transfers_outside_eu = []  # International transfers

class GDPRComplianceManager:
    """Manages GDPR compliance and data subject rights"""
    
    def __init__(self):
        self.compliance_config = config_manager.get_compliance_config()
        self.gdpr_enabled = self.compliance_config.get('gdpr_mode', True)
        self.retention_days = self.compliance_config.get('data_retention_days', 365)
        
        # In-memory storage (use database in production)
        self.gdpr_requests = {}
        self.consent_records = {}
        self.processing_records = {}
        self.data_breaches = {}
        
        # Data mapping for different categories
        self.data_locations = {
            DataCategory.IDENTITY: ["users", "profiles"],
            DataCategory.CONTACT: ["users", "companies"],
            DataCategory.TECHNICAL: ["device_logs", "sessions"],
            DataCategory.BEHAVIORAL: ["analytics", "preferences"],
            DataCategory.CONTENT: ["content_meta", "uploads"],
            DataCategory.LOCATION: ["devices", "heartbeats"]
        }
        
        # Default retention periods by data category (days)
        self.retention_periods = {
            DataCategory.IDENTITY: 365 * 3,  # 3 years
            DataCategory.CONTACT: 365 * 3,   # 3 years
            DataCategory.TECHNICAL: 90,      # 90 days
            DataCategory.BEHAVIORAL: 365,    # 1 year
            DataCategory.CONTENT: 365 * 7,   # 7 years (content may have legal value)
            DataCategory.LOCATION: 30        # 30 days
        }
    
    async def handle_data_subject_request(self, subject_id: str, request_type: DataSubjectRights,
                                        details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle GDPR data subject requests (Article 12-22)"""
        try:
            if not self.gdpr_enabled:
                return {
                    "success": False,
                    "error": "GDPR compliance not enabled"
                }
            
            # Create request record
            request = GDPRRequest(subject_id, request_type, details)
            self.gdpr_requests[request.id] = request
            
            # Log GDPR request
            audit_logger.log_gdpr_request(request_type.value, subject_id, {
                "request_id": request.id,
                "details": details or {}
            })
            
            # Process request based on type
            if request_type == DataSubjectRights.ACCESS:
                response = await self._process_access_request(request)
            elif request_type == DataSubjectRights.RECTIFICATION:
                response = await self._process_rectification_request(request)
            elif request_type == DataSubjectRights.ERASURE:
                response = await self._process_erasure_request(request)
            elif request_type == DataSubjectRights.PORTABILITY:
                response = await self._process_portability_request(request)
            elif request_type == DataSubjectRights.RESTRICTION:
                response = await self._process_restriction_request(request)
            elif request_type == DataSubjectRights.OBJECTION:
                response = await self._process_objection_request(request)
            else:
                response = {
                    "success": False,
                    "error": f"Unsupported request type: {request_type.value}"
                }
            
            # Update request status
            request.processed_at = datetime.now(timezone.utc)
            request.status = "completed" if response.get("success") else "failed"
            request.response_data = response
            
            # Add request tracking info to response
            response["request_id"] = request.id
            response["processed_at"] = request.processed_at.isoformat()
            
            return response
            
        except Exception as e:
            logger.error(f"GDPR request processing failed: {e}")
            audit_logger.log_privacy_event("gdpr_request_error", {
                "subject_id": subject_id,
                "request_type": request_type.value,
                "error": str(e)
            })
            
            return {
                "success": False,
                "error": "Internal processing error"
            }
    
    async def _process_access_request(self, request: GDPRRequest) -> Dict[str, Any]:
        """Process Article 15: Right of access by the data subject"""
        try:
            subject_id = request.subject_id
            personal_data = {}
            
            # Collect data from all categories
            for category in DataCategory:
                category_data = await self._extract_personal_data(subject_id, category)
                if category_data:
                    personal_data[category.value] = category_data
            
            # Get processing information
            processing_info = await self._get_processing_information(subject_id)
            
            # Get consent records
            consent_info = self._get_consent_information(subject_id)
            
            # Prepare response according to GDPR Article 15
            response_data = {
                "subject_id": subject_id,
                "personal_data": personal_data,
                "processing_purposes": processing_info.get("purposes", []),
                "data_categories": list(personal_data.keys()),
                "recipients": processing_info.get("recipients", []),
                "retention_period": processing_info.get("retention_period"),
                "rights_information": self._get_rights_information(),
                "consent_records": consent_info,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            return {
                "success": True,
                "data": response_data,
                "format": "json",
                "message": "Personal data exported successfully"
            }
            
        except Exception as e:
            logger.error(f"Access request processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_erasure_request(self, request: GDPRRequest) -> Dict[str, Any]:
        """Process Article 17: Right to erasure (right to be forgotten)"""
        try:
            subject_id = request.subject_id
            details = request.details or {}
            
            # Check if erasure is legally required
            erasure_grounds = details.get("grounds", "request")
            
            # Verify if we can legally erase the data
            legal_check = await self._check_erasure_legality(subject_id, erasure_grounds)
            if not legal_check["can_erase"]:
                return {
                    "success": False,
                    "error": "Erasure not permitted",
                    "reasons": legal_check["reasons"]
                }
            
            # Perform data erasure
            erased_data = {}
            for category in DataCategory:
                if self._can_erase_category(category, erasure_grounds):
                    result = await self._erase_personal_data(subject_id, category)
                    erased_data[category.value] = result
            
            # Update consent records
            await self._revoke_all_consent(subject_id)
            
            # Log erasure completion
            audit_logger.log_gdpr_request("data_erased", subject_id, {
                "erased_categories": list(erased_data.keys()),
                "grounds": erasure_grounds
            })
            
            return {
                "success": True,
                "erased_data": erased_data,
                "message": "Data erasure completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Erasure request processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_portability_request(self, request: GDPRRequest) -> Dict[str, Any]:
        """Process Article 20: Right to data portability"""
        try:
            subject_id = request.subject_id
            
            # Only include data processed based on consent or contract
            portable_data = {}
            
            for category in DataCategory:
                # Check if data is portable (consent or contract basis)
                if self._is_data_portable(subject_id, category):
                    category_data = await self._extract_personal_data(subject_id, category)
                    if category_data:
                        portable_data[category.value] = category_data
            
            # Format data in structured, commonly used format (JSON)
            export_data = {
                "subject_id": subject_id,
                "export_date": datetime.now(timezone.utc).isoformat(),
                "format_version": "1.0",
                "data": portable_data
            }
            
            return {
                "success": True,
                "portable_data": export_data,
                "format": "json",
                "message": "Portable data exported successfully"
            }
            
        except Exception as e:
            logger.error(f"Portability request processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_rectification_request(self, request: GDPRRequest) -> Dict[str, Any]:
        """Process Article 16: Right to rectification"""
        try:
            subject_id = request.subject_id
            corrections = request.details.get("corrections", {})
            
            if not corrections:
                return {
                    "success": False,
                    "error": "No corrections specified"
                }
            
            updated_fields = {}
            for field, new_value in corrections.items():
                try:
                    # Update the field (implementation depends on data structure)
                    success = await self._update_personal_data_field(subject_id, field, new_value)
                    updated_fields[field] = {
                        "success": success,
                        "new_value": new_value if success else None
                    }
                except Exception as e:
                    updated_fields[field] = {
                        "success": False,
                        "error": str(e)
                    }
            
            return {
                "success": True,
                "updated_fields": updated_fields,
                "message": "Data rectification completed"
            }
            
        except Exception as e:
            logger.error(f"Rectification request processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_restriction_request(self, request: GDPRRequest) -> Dict[str, Any]:
        """Process Article 18: Right to restriction of processing"""
        try:
            subject_id = request.subject_id
            restriction_reason = request.details.get("reason", "user_request")
            
            # Mark data for restricted processing
            restricted_categories = []
            for category in DataCategory:
                if await self._restrict_data_processing(subject_id, category, restriction_reason):
                    restricted_categories.append(category.value)
            
            return {
                "success": True,
                "restricted_categories": restricted_categories,
                "message": "Data processing restriction applied"
            }
            
        except Exception as e:
            logger.error(f"Restriction request processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_objection_request(self, request: GDPRRequest) -> Dict[str, Any]:
        """Process Article 21: Right to object"""
        try:
            subject_id = request.subject_id
            objection_grounds = request.details.get("grounds", "general_objection")
            
            # Stop processing based on legitimate interests
            stopped_processing = []
            for category in DataCategory:
                if await self._stop_legitimate_interest_processing(subject_id, category):
                    stopped_processing.append(category.value)
            
            return {
                "success": True,
                "stopped_processing": stopped_processing,
                "message": "Processing objection handled"
            }
            
        except Exception as e:
            logger.error(f"Objection request processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def manage_consent(self, subject_id: str, purpose: ProcessingPurpose,
                           data_categories: List[DataCategory], action: str,
                           consent_text: str = "") -> Dict[str, Any]:
        """Manage user consent for data processing"""
        try:
            if action == "give":
                consent = ConsentRecord(subject_id, purpose, data_categories)
                consent.consent_text = consent_text
                self.consent_records[consent.id] = consent
                
                # Log consent given
                audit_logger.log_privacy_event("consent_given", {
                    "subject_id": subject_id,
                    "purpose": purpose.value,
                    "categories": [cat.value for cat in data_categories]
                })
                
                return {
                    "success": True,
                    "consent_id": consent.id,
                    "status": "given"
                }
                
            elif action == "withdraw":
                # Find and withdraw consent
                for consent in self.consent_records.values():
                    if (consent.subject_id == subject_id and 
                        consent.purpose == purpose and
                        consent.status == ConsentStatus.GIVEN):
                        
                        consent.status = ConsentStatus.WITHDRAWN
                        consent.withdrawn_at = datetime.now(timezone.utc)
                        
                        # Log consent withdrawal
                        audit_logger.log_privacy_event("consent_withdrawn", {
                            "subject_id": subject_id,
                            "purpose": purpose.value,
                            "consent_id": consent.id
                        })
                        
                        return {
                            "success": True,
                            "consent_id": consent.id,
                            "status": "withdrawn"
                        }
                
                return {
                    "success": False,
                    "error": "No active consent found to withdraw"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown consent action: {action}"
                }
                
        except Exception as e:
            logger.error(f"Consent management failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def report_data_breach(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Report and handle data breach (Article 33-34)"""
        try:
            breach_id = str(uuid.uuid4())
            breach_time = datetime.now(timezone.utc)
            
            breach_record = {
                "id": breach_id,
                "reported_at": breach_time,
                "incident_date": incident_data.get("incident_date", breach_time.isoformat()),
                "description": incident_data.get("description", ""),
                "affected_data_categories": incident_data.get("affected_categories", []),
                "affected_subjects_count": incident_data.get("affected_count", 0),
                "likelihood_of_harm": incident_data.get("harm_likelihood", "unknown"),
                "measures_taken": incident_data.get("measures", []),
                "status": "reported"
            }
            
            self.data_breaches[breach_id] = breach_record
            
            # Log breach
            audit_logger.log_security_event("data_breach_reported", {
                "breach_id": breach_id,
                "affected_count": breach_record["affected_subjects_count"],
                "categories": breach_record["affected_data_categories"]
            }, severity=AuditSeverity.CRITICAL)
            
            # Check if supervisory authority notification required (within 72 hours)
            if self._requires_authority_notification(breach_record):
                # TODO: Implement automatic notification to DPA
                breach_record["authority_notification_required"] = True
                breach_record["notification_deadline"] = (breach_time + timedelta(hours=72)).isoformat()
            
            # Check if data subjects notification required
            if self._requires_subject_notification(breach_record):
                breach_record["subject_notification_required"] = True
                # TODO: Implement subject notification
            
            return {
                "success": True,
                "breach_id": breach_id,
                "authority_notification_required": breach_record.get("authority_notification_required", False),
                "subject_notification_required": breach_record.get("subject_notification_required", False)
            }
            
        except Exception as e:
            logger.error(f"Data breach reporting failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Helper methods (implementation stubs - would need actual database integration)
    
    async def _extract_personal_data(self, subject_id: str, category: DataCategory) -> Dict[str, Any]:
        """Extract personal data for specific category"""
        # TODO: Implement actual data extraction from databases
        return {"placeholder": f"Data for {category.value}"}
    
    async def _erase_personal_data(self, subject_id: str, category: DataCategory) -> Dict[str, Any]:
        """Erase personal data for specific category"""
        # TODO: Implement actual data erasure
        return {"erased": True, "category": category.value}
    
    async def _check_erasure_legality(self, subject_id: str, grounds: str) -> Dict[str, Any]:
        """Check if data erasure is legally permitted"""
        # Check for legal obligations, public interest, etc.
        return {"can_erase": True, "reasons": []}
    
    def _can_erase_category(self, category: DataCategory, grounds: str) -> bool:
        """Check if specific data category can be erased"""
        # Some data may need to be retained for legal reasons
        return True
    
    def _is_data_portable(self, subject_id: str, category: DataCategory) -> bool:
        """Check if data category is portable under GDPR Article 20"""
        # Only data processed based on consent or contract is portable
        return category in [DataCategory.IDENTITY, DataCategory.CONTENT, DataCategory.BEHAVIORAL]
    
    async def _update_personal_data_field(self, subject_id: str, field: str, value: Any) -> bool:
        """Update specific data field"""
        # TODO: Implement actual data update
        return True
    
    async def _restrict_data_processing(self, subject_id: str, category: DataCategory, reason: str) -> bool:
        """Mark data for restricted processing"""
        # TODO: Implement processing restriction
        return True
    
    async def _stop_legitimate_interest_processing(self, subject_id: str, category: DataCategory) -> bool:
        """Stop processing based on legitimate interests"""
        # TODO: Implement processing stop
        return True
    
    async def _revoke_all_consent(self, subject_id: str):
        """Revoke all consent records for subject"""
        for consent in self.consent_records.values():
            if consent.subject_id == subject_id and consent.status == ConsentStatus.GIVEN:
                consent.status = ConsentStatus.WITHDRAWN
                consent.withdrawn_at = datetime.now(timezone.utc)
    
    async def _get_processing_information(self, subject_id: str) -> Dict[str, Any]:
        """Get information about data processing"""
        return {
            "purposes": ["service_provision", "analytics"],
            "recipients": ["internal_team", "cloud_providers"],
            "retention_period": f"{self.retention_days} days"
        }
    
    def _get_consent_information(self, subject_id: str) -> List[Dict[str, Any]]:
        """Get consent records for subject"""
        consent_info = []
        for consent in self.consent_records.values():
            if consent.subject_id == subject_id:
                consent_info.append({
                    "id": consent.id,
                    "purpose": consent.purpose.value,
                    "categories": [cat.value for cat in consent.data_categories],
                    "status": consent.status.value,
                    "given_at": consent.given_at.isoformat(),
                    "withdrawn_at": consent.withdrawn_at.isoformat() if consent.withdrawn_at else None
                })
        return consent_info
    
    def _get_rights_information(self) -> Dict[str, str]:
        """Get information about GDPR rights"""
        return {
            "access": "You can request a copy of your personal data",
            "rectification": "You can request correction of inaccurate data",
            "erasure": "You can request deletion of your data",
            "restriction": "You can request restriction of processing",
            "portability": "You can request your data in a portable format",
            "objection": "You can object to certain processing activities",
            "complaint": "You can file a complaint with supervisory authorities"
        }
    
    def _requires_authority_notification(self, breach_record: Dict[str, Any]) -> bool:
        """Check if breach requires supervisory authority notification"""
        # High-risk breaches require notification within 72 hours
        return breach_record.get("likelihood_of_harm", "unknown") in ["high", "very_high"]
    
    def _requires_subject_notification(self, breach_record: Dict[str, Any]) -> bool:
        """Check if breach requires data subject notification"""
        # High risk to rights and freedoms requires subject notification
        return (breach_record.get("likelihood_of_harm", "unknown") == "very_high" or
                breach_record.get("affected_subjects_count", 0) > 100)

# Global GDPR compliance manager
gdpr_manager = GDPRComplianceManager()