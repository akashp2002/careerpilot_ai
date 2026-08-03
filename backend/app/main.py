import os
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.agents.graph import build_graph
from app.agents.state import GraphState
from langgraph.types import Command    
import uuid
import pdfplumber
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.parser import parse_resume_text
from app.core.verifier import verify_resume
from app.models.db_models import CandidateProfile
from app.models.resume import ParsedResume, VerifiedResume
from sqlalchemy import select
from app.core.database import get_db, AsyncSession
from app.models.db_models import CandidateProfile
from app.models.resume import JobSearchRequest
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware



LANGGRAPH_DB_URL = os.getenv("DATABASE_URL").replace("+asyncpg", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncPostgresSaver.from_conn_string(LANGGRAPH_DB_URL) as checkpointer:
        await checkpointer.setup()
        app.state.graph = build_graph(checkpointer)
        yield
    # connection closes automatically when the app shuts down


app = FastAPI(title="CareerPilot AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/api/resume/upload", response_model=VerifiedResume)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    raw_text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                raw_text += page_text + "\n"

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from PDF. It may be a scanned image.")

    try:
        parsed = parse_resume_text(raw_text)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    verified = verify_resume(parsed)
    user_id = "demo_user"  # placeholder until auth is added

    existing_profile = await db.scalar(
        select(CandidateProfile).where(CandidateProfile.user_id == user_id)
    )

    if existing_profile is None:
        existing_profile = CandidateProfile(user_id=user_id)
        db.add(existing_profile)

    existing_profile.basics = parsed.basics.model_dump()
    existing_profile.skills = parsed.skills
    existing_profile.experience = [exp.model_dump() for exp in parsed.experience]
    existing_profile.education = [edu.model_dump() for edu in parsed.education]
    existing_profile.projects = [proj.model_dump() for proj in parsed.projects]
    existing_profile.raw_text = parsed.raw_text
    existing_profile.verification_flags = [flag.model_dump() for flag in verified.flags]
    existing_profile.flagged_count = verified.flagged_count

    await db.commit()
    await db.refresh(existing_profile)

    return verified

@app.post("/api/jobs/search")
async def start_job_search(request: JobSearchRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == request.user_id)
    )
    profile_row = result.scalar_one_or_none()

    if profile_row is None:
        raise HTTPException(status_code=404, detail=f"No candidate profile found for user_id '{request.user_id}'. Upload a resume first.")

    candidate_profile = {
        "basics": profile_row.basics,
        "skills": profile_row.skills,
        "experience": profile_row.experience,
        "education": profile_row.education,
        "projects": profile_row.projects,
    }

    preferences = {
        "role": request.role,
        "locations": request.locations,
        "salary_min": request.salary_min,
        "salary_max": request.salary_max,
        "remote_ok": request.remote_ok,
    }

    graph = app.state.graph
    session_id = f"{request.user_id}:{uuid.uuid4()}"
    config = {"configurable": {"thread_id": session_id}}

    initial_state: GraphState = {
        "candidate_profile": candidate_profile,
        "preferences": preferences,
        "raw_listings": [],
        "analyzed_jobs": [],
        "ranked_jobs": [],
        "explanations": {},
        "iteration": 0,
        "user_feedback": None,
    }

    graph_result = await graph.ainvoke(initial_state, config=config)
    graph_result["_session_id"] = session_id
    return graph_result

class JobResumeRequest(BaseModel):
    session_id: str
    approved: bool
    updated_preferences: Optional[dict] = None


@app.post("/api/jobs/resume")
async def resume_job_search(request: JobResumeRequest):
    graph = app.state.graph
    config = {"configurable": {"thread_id": request.session_id}}

    existing_state = await graph.aget_state(config)
    if not existing_state or not existing_state.next:
        raise HTTPException(
            status_code=404,
            detail=f"No active paused session found for session_id '{request.session_id}'. It may be invalid, already completed, or expired."
        )

    resume_payload = {"approved": request.approved}
    if not request.approved and request.updated_preferences:
        resume_payload["updated_preferences"] = request.updated_preferences

    result = await graph.ainvoke(
        Command(resume=resume_payload),
        config=config,
    )
    return result