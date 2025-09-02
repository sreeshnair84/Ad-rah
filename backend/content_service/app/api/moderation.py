from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File
from app.auth import get_current_user, get_user_company_context
from app.models import ModerationResult, Review
from app.repo import repo
import uuid
import os
import tempfile
from typing import Optional
from app.moderation_worker import worker
from app.utils.serialization import safe_json_response
from app.services.ai_service_manager import get_ai_service_manager
from app.services.ai_agent_framework import AnalysisRequest, ContentType, ModerationAction
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.post("/analyze/text", response_model=Review)
async def analyze_text_content(
    content_id: str = Form(...),
    text_content: str = Form(...),
    metadata: Optional[str] = Form(None),
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Analyze text content using AI agents"""
    
    # Check if user has permission to analyze content
    current_user_id = current_user.get("id")
    is_platform_admin = company_context["is_platform_admin"]
    user_can_analyze = is_platform_admin
    
    if not is_platform_admin:
        # Check if user has APPROVER role or higher in any company
        accessible_companies = company_context["accessible_companies"]
        for company in accessible_companies:
            company_id = company.get("id")
            if company_id:
                user_role = await repo.get_user_role_in_company(current_user_id, company_id)
                if user_role:
                    role_details = user_role.get("role_details", {})
                    company_role_type = role_details.get("company_role_type")
                    if company_role_type in ["COMPANY_ADMIN", "APPROVER"]:
                        user_can_analyze = True
                        break
    
    if not user_can_analyze:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only approvers and admins can analyze content"
        )
    try:
        # Get AI service manager
        service_manager = get_ai_service_manager()
        pipeline = service_manager.get_pipeline()
        
        # Create analysis request
        request = AnalysisRequest(
            content_id=content_id,
            content_type=ContentType.TEXT,
            text_content=text_content,
            metadata={"source": "text_upload"} if not metadata else eval(metadata)
        )
        
        # Perform AI analysis
        result = await pipeline.process_content(request)
        
        # Convert to Review model
        review = Review(
            id=str(uuid.uuid4()),
            content_id=content_id,
            ai_confidence=result.confidence,
            action=result.action.value,
            ai_analysis={
                "reasoning": result.reasoning,
                "categories": result.categories,
                "safety_scores": result.safety_scores,
                "quality_score": result.quality_score,
                "brand_safety_score": result.brand_safety_score,
                "compliance_score": result.compliance_score,
                "concerns": result.concerns,
                "suggestions": result.suggestions,
                "model_used": result.model_used,
                "processing_time": result.processing_time
            }
        )
        
        # Save to database
        saved = await repo.save_review(review.model_dump())
        
        logger.info(f"Text content {content_id} analyzed: {result.action} (confidence: {result.confidence:.3f})")
        return saved
        
    except Exception as e:
        logger.error(f"Error analyzing text content {content_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/image", response_model=Review)
async def analyze_image_content(
    content_id: str = Form(...),
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Analyze image content using AI agents"""
    
    # Check if user has permission to analyze content (same logic as text)
    current_user_id = current_user.get("id")
    is_platform_admin = company_context["is_platform_admin"]
    user_can_analyze = is_platform_admin
    
    if not is_platform_admin:
        # Check if user has APPROVER role or higher in any company
        accessible_companies = company_context["accessible_companies"]
        for company in accessible_companies:
            company_id = company.get("id")
            if company_id:
                user_role = await repo.get_user_role_in_company(current_user_id, company_id)
                if user_role:
                    role_details = user_role.get("role_details", {})
                    company_role_type = role_details.get("company_role_type")
                    if company_role_type in ["COMPANY_ADMIN", "APPROVER"]:
                        user_can_analyze = True
                        break
    
    if not user_can_analyze:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only approvers and admins can analyze content"
        )
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported image format")
        
        # Save uploaded file temporarily
        file_ext = ".jpg"  # Default extension
        if file.filename:
            file_ext = os.path.splitext(file.filename)[1] or ".jpg"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Get AI service manager
            service_manager = get_ai_service_manager()
            pipeline = service_manager.get_pipeline()
            
            # Create analysis request
            request = AnalysisRequest(
                content_id=content_id,
                content_type=ContentType.IMAGE,
                file_path=temp_file_path,
                metadata={"source": "image_upload", "filename": file.filename} if not metadata else eval(metadata)
            )
            
            # Perform AI analysis
            result = await pipeline.process_content(request)
            
            # Convert to Review model
            review = Review(
                id=str(uuid.uuid4()),
                content_id=content_id,
                ai_confidence=result.confidence,
                action=result.action.value,
                ai_analysis={
                    "reasoning": result.reasoning,
                    "categories": result.categories,
                    "safety_scores": result.safety_scores,
                    "quality_score": result.quality_score,
                    "brand_safety_score": result.brand_safety_score,
                    "compliance_score": result.compliance_score,
                    "concerns": result.concerns,
                    "suggestions": result.suggestions,
                    "model_used": result.model_used,
                    "processing_time": result.processing_time,
                    "file_info": {
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "size": len(content)
                    }
                }
            )
            
            # Save to database
            saved = await repo.save_review(review.model_dump())
            
            logger.info(f"Image content {content_id} analyzed: {result.action} (confidence: {result.confidence:.3f})")
            return saved
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error analyzing image content {content_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/video", response_model=Review)
async def analyze_video_content(
    content_id: str = Form(...),
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Analyze video content using AI agents"""
    
    # Check if user has permission to analyze content (same logic as text)
    current_user_id = current_user.get("id")
    is_platform_admin = company_context["is_platform_admin"]
    user_can_analyze = is_platform_admin
    
    if not is_platform_admin:
        # Check if user has APPROVER role or higher in any company
        accessible_companies = company_context["accessible_companies"]
        for company in accessible_companies:
            company_id = company.get("id")
            if company_id:
                user_role = await repo.get_user_role_in_company(current_user_id, company_id)
                if user_role:
                    role_details = user_role.get("role_details", {})
                    company_role_type = role_details.get("company_role_type")
                    if company_role_type in ["COMPANY_ADMIN", "APPROVER"]:
                        user_can_analyze = True
                        break
    
    if not user_can_analyze:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only approvers and admins can analyze content"
        )
    try:
        # Validate file type
        allowed_types = ["video/mp4", "video/mpeg", "video/quicktime", "video/webm"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported video format")
        
        # Check file size (limit to 100MB for processing)
        content = await file.read()
        if len(content) > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Video file too large (max 100MB)")
        
        # Save uploaded file temporarily
        file_ext = ".mp4"  # Default extension
        if file.filename:
            file_ext = os.path.splitext(file.filename)[1] or ".mp4"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Get AI service manager
            service_manager = get_ai_service_manager()
            pipeline = service_manager.get_pipeline()
            
            # Create analysis request
            request = AnalysisRequest(
                content_id=content_id,
                content_type=ContentType.VIDEO,
                file_path=temp_file_path,
                metadata={"source": "video_upload", "filename": file.filename} if not metadata else eval(metadata)
            )
            
            # Perform AI analysis
            result = await pipeline.process_content(request)
            
            # Convert to Review model
            review = Review(
                id=str(uuid.uuid4()),
                content_id=content_id,
                ai_confidence=result.confidence,
                action=result.action.value,
                ai_analysis={
                    "reasoning": result.reasoning,
                    "categories": result.categories,
                    "safety_scores": result.safety_scores,
                    "quality_score": result.quality_score,
                    "brand_safety_score": result.brand_safety_score,
                    "compliance_score": result.compliance_score,
                    "concerns": result.concerns,
                    "suggestions": result.suggestions,
                    "model_used": result.model_used,
                    "processing_time": result.processing_time,
                    "file_info": {
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "size": len(content)
                    }
                }
            )
            
            # Save to database
            saved = await repo.save_review(review.model_dump())
            
            logger.info(f"Video content {content_id} analyzed: {result.action} (confidence: {result.confidence:.3f})")
            return saved
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error analyzing video content {content_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/agents/status")
async def get_agents_status():
    """Get status of all AI agents"""
    try:
        service_manager = get_ai_service_manager()
        status = service_manager.get_status()
        health_status = await service_manager.health_check_all()
        
        # Combine status and health information
        for agent_name in status["agents"]:
            agent_key = f"{agent_name}_agent"
            status["agents"][agent_name]["health"] = health_status.get(agent_key, False)
        
        return status
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/agents/{agent_name}/switch")
async def switch_primary_agent(agent_name: str):
    """Switch to a different primary AI agent"""
    try:
        service_manager = get_ai_service_manager()
        success = service_manager.switch_primary_agent(agent_name)
        
        if success:
            return {"message": f"Switched to {agent_name}", "success": True}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to switch to {agent_name}")
    except Exception as e:
        logger.error(f"Error switching agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Switch failed: {str(e)}")


@router.post("/agents/{agent_name}/enable")
async def enable_agent(agent_name: str):
    """Enable an AI agent"""
    try:
        service_manager = get_ai_service_manager()
        success = service_manager.enable_agent(agent_name)
        
        if success:
            return {"message": f"Enabled {agent_name}", "success": True}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to enable {agent_name}")
    except Exception as e:
        logger.error(f"Error enabling agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enable failed: {str(e)}")


@router.post("/agents/{agent_name}/disable")
async def disable_agent(agent_name: str):
    """Disable an AI agent"""
    try:
        service_manager = get_ai_service_manager()
        success = service_manager.disable_agent(agent_name)
        
        if success:
            return {"message": f"Disabled {agent_name}", "success": True}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to disable {agent_name}")
    except Exception as e:
        logger.error(f"Error disabling agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Disable failed: {str(e)}")


@router.post("/enqueue", response_model=Review)
async def enqueue_for_moderation(content_id: str = Form(...), text_content: str = Form(None)):
    """Legacy endpoint - now uses AI agents instead of simulation"""
    try:
        if text_content:
            # Use the new AI analysis for text content
            return await analyze_text_content(content_id, text_content)
        else:
            # Fallback to simple review creation for backward compatibility
            review = Review(
                id=str(uuid.uuid4()),
                content_id=content_id,
                ai_confidence=0.5,
                action="needs_review"
            )
            saved = await repo.save_review(review.model_dump())
            return saved
    except Exception as e:
        logger.error(f"Error in legacy enqueue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enqueue failed: {str(e)}")


@router.get("/queue")
async def list_queue():
    reviews = await repo.list_reviews()
    return safe_json_response(reviews)


@router.post("/job/enqueue")
async def enqueue_job(content_id: str = Form(...)):
    job_id = await worker.enqueue(content_id)
    return {"job_id": job_id}


@router.get("/job/{job_id}")
async def job_status(job_id: str):
    status = await worker.get_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="job not found")
    return status


@router.post("/job/{job_id}/wait")
async def job_wait(job_id: str, timeout: float = 5.0):
    try:
        job = await worker.wait_for_job(job_id, timeout=timeout)
        return job
    except KeyError:
        raise HTTPException(status_code=404, detail="job not found")
    except TimeoutError:
        raise HTTPException(status_code=504, detail="job did not complete in time")


@router.post("/{review_id}/decision")
async def post_decision(
    review_id: str, 
    decision: str = Form(...), 
    reviewer_id: str = Form(None), 
    notes: str = Form(None),
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    # Check if user has permission to make moderation decisions
    current_user_id = current_user.get("id")
    is_platform_admin = company_context["is_platform_admin"]
    user_can_moderate = is_platform_admin
    
    if not is_platform_admin:
        # Check if user has APPROVER role or higher in any company
        accessible_companies = company_context["accessible_companies"]
        for company in accessible_companies:
            company_id = company.get("id")
            if company_id:
                user_role = await repo.get_user_role_in_company(current_user_id, company_id)
                if user_role:
                    role_details = user_role.get("role_details", {})
                    company_role_type = role_details.get("company_role_type")
                    if company_role_type in ["COMPANY_ADMIN", "APPROVER"]:
                        user_can_moderate = True
                        break
    
    if not user_can_moderate:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only approvers and admins can make moderation decisions"
        )
    
    reviews = await repo.list_reviews()
    item = next((r for r in reviews if r.get("id") == review_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="review not found")
    
    # Get content to check company access
    content_id = item.get("content_id")
    if content_id and not is_platform_admin:
        content = await repo.get_content_meta(content_id)
        if content:
            owner_id = content.get("owner_id")
            if owner_id:
                can_access = await repo.check_content_access_permission(
                    current_user_id, owner_id, "edit"
                )
                if not can_access:
                    raise HTTPException(
                        status_code=403,
                        detail="Access denied: Cannot moderate content from outside your company"
                    )
    
    item["action"] = "manual_approve" if decision == "approve" else "manual_reject"
    item["reviewer_id"] = reviewer_id or current_user_id
    item["notes"] = notes
    saved = await repo.save_review(item)
    return saved


@router.post("/content/{content_id}/decision")
async def post_decision_by_content_id(
    content_id: str, 
    decision: str = Form(...), 
    reviewer_id: str = Form(None), 
    notes: str = Form(None),
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Post moderation decision using content_id instead of review_id"""
    try:
        # Check if user has permission to make moderation decisions
        current_user_id = current_user.get("id")
        is_platform_admin = company_context["is_platform_admin"]
        user_can_moderate = is_platform_admin
        
        if not is_platform_admin:
            # Check if user has APPROVER role or higher in any company
            accessible_companies = company_context["accessible_companies"]
            for company in accessible_companies:
                company_id = company.get("id")
                if company_id:
                    user_role = await repo.get_user_role_in_company(current_user_id, company_id)
                    if user_role:
                        role_details = user_role.get("role_details", {})
                        company_role_type = role_details.get("company_role_type")
                        if company_role_type in ["COMPANY_ADMIN", "APPROVER"]:
                            user_can_moderate = True
                            break
        
        if not user_can_moderate:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Only approvers and admins can make moderation decisions"
            )
        
        # Check if user can access this content
        if not is_platform_admin:
            content = await repo.get_content_meta(content_id)
            if content:
                owner_id = content.get("owner_id")
                if owner_id:
                    can_access = await repo.check_content_access_permission(
                        current_user_id, owner_id, "edit"
                    )
                    if not can_access:
                        raise HTTPException(
                            status_code=403,
                            detail="Access denied: Cannot moderate content from outside your company"
                        )
        # Find the review record for this content
        reviews = await repo.list_reviews()
        item = next((r for r in reviews if r.get("content_id") == content_id), None)
        
        if not item:
            # If no review exists, create one
            import uuid
            item = {
                "id": str(uuid.uuid4()),
                "content_id": content_id,
                "action": "needs_review",
                "ai_confidence": None,
                "reviewer_id": None,
                "notes": None
            }
        
        # Update the review with the decision  
        item["action"] = "manual_approve" if decision == "approve" else "manual_reject"
        item["reviewer_id"] = reviewer_id or current_user_id
        item["notes"] = notes
        
        # Save the review - use the Review model for validation
        from app.models import Review
        
        # Clean up the item before creating the model
        clean_item = {k: v for k, v in item.items() if k in Review.model_fields}
        review_model = Review(**clean_item)
        
        # Save using the model
        saved = await repo.save_review(review_model.model_dump())
        
        # Ensure we clean the saved data before returning
        from app.utils.serialization import ensure_string_id
        clean_saved = ensure_string_id(saved) if saved else {}
        return safe_json_response(clean_saved)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing decision: {e}")


@router.get("/pending")
async def get_pending_reviews(
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Get reviews that need manual attention with company filtering"""
    try:
        current_user_id = current_user.get("id")
        is_platform_admin = company_context["is_platform_admin"]
        
        reviews = await repo.list_reviews()
        # Filter for reviews that need manual review
        pending_reviews = [r for r in reviews if r.get("action") == "needs_review"]
        
        # Apply company filtering if not platform admin
        if not is_platform_admin:
            filtered_reviews = []
            for review in pending_reviews:
                content_id = review.get("content_id")
                if content_id:
                    content = await repo.get_content_meta(content_id)
                    if content:
                        owner_id = content.get("owner_id")
                        if owner_id:
                            can_access = await repo.check_content_access_permission(
                                current_user_id, owner_id, "view"
                            )
                            if can_access:
                                filtered_reviews.append(review)
                    else:
                        # Include reviews without content (for backward compatibility)
                        filtered_reviews.append(review)
                else:
                    # Include reviews without content_id (for backward compatibility)
                    filtered_reviews.append(review)
            pending_reviews = filtered_reviews
        
        # Clean all pending reviews to handle ObjectId serialization
        from app.utils.serialization import ensure_string_id
        cleaned_reviews = [ensure_string_id(review) for review in pending_reviews]
        
        return safe_json_response(cleaned_reviews)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to get pending reviews: {e}")
