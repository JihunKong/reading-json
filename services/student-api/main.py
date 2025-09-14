"""
Korean Reading Comprehension - Student API Service
FastAPI-based REST API for student learning interface
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
import asyncio
import json
import logging
from datetime import datetime, timedelta
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import select, update, and_, or_, func
import redis.asyncio as redis
from pydantic import BaseModel, EmailStr, Field

# Import local modules
from auth import get_current_user, create_access_token, verify_password, get_password_hash
from models import User, StudentProfile, ContentItem, Submission, GradingResult, LearningProgress
from schemas import (
    UserCreate, UserLogin, UserResponse,
    ContentResponse, SubmissionCreate, SubmissionResponse,
    GradingResponse, ProgressResponse, LearningPathResponse
)
from grading import GradingService
from recommendations import RecommendationEngine
from websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql+asyncpg://postgres:postgres123@postgres:5432/reading_db"
REDIS_URL = "redis://default:redis123@redis:6379/0"

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False, pool_size=20, max_overflow=40)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Redis client
redis_client = None

# WebSocket manager
ws_manager = WebSocketManager()

# Grading service
grading_service = None

# Recommendation engine
recommendation_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global redis_client, grading_service, recommendation_engine
    
    # Startup
    logger.info("Starting Student API Service...")
    
    # Initialize Redis
    redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
    await redis_client.ping()
    logger.info("Redis connected successfully")
    
    # Initialize services
    grading_service = GradingService(redis_client)
    recommendation_engine = RecommendationEngine(redis_client)
    
    logger.info("Student API Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Student API Service...")
    await redis_client.close()
    logger.info("Student API Service shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Korean Reading Comprehension - Student API",
    description="API for student learning interface",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        async with AsyncSessionLocal() as session:
            await session.execute(select(1))
        
        # Check Redis
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "connected",
                "redis": "connected",
                "websocket": "active"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# Authentication endpoints
@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new student user"""
    try:
        # Check if user exists
        result = await db.execute(
            select(User).where(
                or_(User.email == user_data.email, User.username == user_data.username)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="User with this email or username already exists"
            )
        
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=user_data.email,
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            role="student"
        )
        db.add(user)
        
        # Create student profile
        profile = StudentProfile(
            user_id=user.id,
            grade_level=user_data.grade_level,
            school=user_data.school,
            reading_level=user_data.reading_level or "intermediate"
        )
        db.add(profile)
        
        await db.commit()
        
        # Generate access token
        access_token = create_access_token(data={"sub": user.id})
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            access_token=access_token,
            token_type="bearer"
        )
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/v1/auth/login", response_model=UserResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login user"""
    try:
        # Find user
        result = await db.execute(
            select(User).where(User.username == credentials.username)
        )
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()
        
        # Generate access token
        access_token = create_access_token(data={"sub": user.id})
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            access_token=access_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

# Content endpoints
@app.get("/api/v1/content/next", response_model=ContentResponse)
async def get_next_content(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get next recommended content for the user"""
    try:
        # Get user's learning progress
        result = await db.execute(
            select(LearningProgress).where(
                LearningProgress.user_id == current_user.id
            )
        )
        progress_records = result.scalars().all()
        
        # Get completed content IDs
        completed_ids = [p.content_id for p in progress_records if p.completed]
        
        # Get recommendation from engine
        recommended_id = await recommendation_engine.get_next_content(
            user_id=current_user.id,
            completed_ids=completed_ids,
            db=db
        )
        
        if not recommended_id:
            # Fallback: get any unfinished content
            result = await db.execute(
                select(ContentItem).where(
                    and_(
                        ContentItem.is_active == True,
                        ContentItem.id.notin_(completed_ids) if completed_ids else True
                    )
                ).limit(1)
            )
            content = result.scalar_one_or_none()
        else:
            result = await db.execute(
                select(ContentItem).where(ContentItem.id == recommended_id)
            )
            content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(status_code=404, detail="No content available")
        
        return ContentResponse(
            id=content.id,
            task_type=content.task_type,
            content_data=content.content_data,
            difficulty=content.difficulty,
            topic=content.topic,
            tags=content.tags,
            estimated_time=content.avg_completion_time or 300
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content")

@app.get("/api/v1/content/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific content item"""
    try:
        result = await db.execute(
            select(ContentItem).where(
                and_(
                    ContentItem.id == content_id,
                    ContentItem.is_active == True
                )
            )
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Track content view
        await redis_client.hincrby(
            f"content:views:{content_id}",
            current_user.id,
            1
        )
        
        return ContentResponse(
            id=content.id,
            task_type=content.task_type,
            content_data=content.content_data,
            difficulty=content.difficulty,
            topic=content.topic,
            tags=content.tags,
            estimated_time=content.avg_completion_time or 300
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content")

# Submission endpoints
@app.post("/api/v1/submissions", response_model=SubmissionResponse)
async def submit_answer(
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit answer for grading"""
    try:
        # Create submission
        submission = Submission(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            content_id=submission_data.content_id,
            submission_data=submission_data.answers,
            time_spent=submission_data.time_spent,
            processing_status="pending"
        )
        db.add(submission)
        await db.commit()
        
        # Queue for grading
        await grading_service.queue_submission(submission.id)
        
        # Notify via WebSocket
        await ws_manager.send_to_user(
            current_user.id,
            {
                "type": "submission_received",
                "submission_id": submission.id,
                "status": "processing"
            }
        )
        
        return SubmissionResponse(
            id=submission.id,
            content_id=submission.content_id,
            status="processing",
            submitted_at=submission.submitted_at
        )
        
    except Exception as e:
        logger.error(f"Submission error: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Submission failed")

@app.get("/api/v1/submissions/{submission_id}/feedback", response_model=GradingResponse)
async def get_feedback(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get grading feedback for submission"""
    try:
        # Get submission
        result = await db.execute(
            select(Submission).where(
                and_(
                    Submission.id == submission_id,
                    Submission.user_id == current_user.id
                )
            )
        )
        submission = result.scalar_one_or_none()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Get grading result
        result = await db.execute(
            select(GradingResult).where(GradingResult.submission_id == submission_id)
        )
        grading = result.scalar_one_or_none()
        
        if not grading:
            return GradingResponse(
                submission_id=submission_id,
                status="processing",
                feedback="채점 중입니다..."
            )
        
        return GradingResponse(
            submission_id=submission_id,
            status="completed",
            mcq_score=grading.mcq_score,
            similarity_score=grading.free_text_similarity,
            feedback=grading.feedback_text,
            detailed_analysis=grading.detailed_analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feedback")

# Progress endpoints
@app.get("/api/v1/progress/summary", response_model=ProgressResponse)
async def get_progress_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's learning progress summary"""
    try:
        # Get all progress records
        result = await db.execute(
            select(LearningProgress).where(
                LearningProgress.user_id == current_user.id
            )
        )
        progress_records = result.scalars().all()
        
        # Calculate statistics
        total_attempted = len(progress_records)
        total_completed = sum(1 for p in progress_records if p.completed)
        total_time = sum(p.time_spent_total or 0 for p in progress_records)
        avg_score = sum(p.best_score or 0 for p in progress_records) / max(total_attempted, 1)
        
        # Get recent activity
        recent_result = await db.execute(
            select(Submission)
            .where(Submission.user_id == current_user.id)
            .order_by(Submission.submitted_at.desc())
            .limit(10)
        )
        recent_submissions = recent_result.scalars().all()
        
        return ProgressResponse(
            total_attempted=total_attempted,
            total_completed=total_completed,
            total_time_spent=total_time,
            average_score=round(avg_score, 2),
            current_streak=await _calculate_streak(current_user.id, db),
            recent_activity=[
                {
                    "content_id": s.content_id,
                    "submitted_at": s.submitted_at,
                    "status": s.processing_status
                }
                for s in recent_submissions
            ]
        )
        
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get progress")

# WebSocket endpoint for real-time updates
@app.websocket("/ws/feedback/{user_id}")
async def websocket_feedback(
    websocket: WebSocket,
    user_id: str
):
    """WebSocket for real-time grading feedback"""
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)

# Helper functions
async def _calculate_streak(user_id: str, db: AsyncSession) -> int:
    """Calculate user's current learning streak"""
    result = await db.execute(
        select(func.date(Submission.submitted_at))
        .where(Submission.user_id == user_id)
        .group_by(func.date(Submission.submitted_at))
        .order_by(func.date(Submission.submitted_at).desc())
    )
    dates = [row[0] for row in result.all()]
    
    if not dates:
        return 0
    
    streak = 1
    for i in range(1, len(dates)):
        if dates[i-1] - dates[i] == timedelta(days=1):
            streak += 1
        else:
            break
    
    return streak

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)