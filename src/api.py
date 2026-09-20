from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import json
from contextlib import asynccontextmanager

from .database import get_db, init_db, User, Ticket, Decision
from .auth import get_password_hash, verify_password, create_access_token, get_current_user
from .decision import generate_decision

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database on startup
    await init_db()
    yield

app = FastAPI(title="Support Ticket AI API", lifespan=lifespan)

# Pydantic models for request/response validation
class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TicketCreate(BaseModel):
    message: str

class DecisionResponse(BaseModel):
    action: str
    reason: str
    confidence: float
    sources: list[str]

class TicketResponse(BaseModel):
    id: int
    user_id: int
    message: str
    decision: DecisionResponse | dict | None = None
    
    class Config:
        from_attributes = True

@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, password_hash=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/tickets", response_model=TicketResponse)
async def create_ticket(ticket: TicketCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Create ticket
    new_ticket = Ticket(user_id=current_user.id, message=ticket.message)
    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)
    
    # Generate AI Decision
    decision_data = generate_decision(ticket.message)
    
    # Save Decision
    new_decision = Decision(
        ticket_id=new_ticket.id,
        action=decision_data.get("action", "UNKNOWN"),
        reason=decision_data.get("reason", ""),
        confidence=float(decision_data.get("confidence", 0.0)),
        sources=decision_data.get("sources", [])
    )
    db.add(new_decision)
    await db.commit()
    await db.refresh(new_decision)
    
    return {
        "id": new_ticket.id,
        "user_id": new_ticket.user_id,
        "message": new_ticket.message,
        "decision": {
            "action": new_decision.action,
            "reason": new_decision.reason,
            "confidence": new_decision.confidence,
            "sources": new_decision.sources
        }
    }

@app.get("/tickets", response_model=list[TicketResponse])
async def read_tickets(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.user_id == current_user.id))
    tickets = result.scalars().all()
    
    response = []
    for t in tickets:
        d_result = await db.execute(select(Decision).where(Decision.ticket_id == t.id))
        decision = d_result.scalars().first()
        decision_dict = None
        if decision:
            decision_dict = {
                "action": decision.action,
                "reason": decision.reason,
                "confidence": decision.confidence,
                "sources": decision.sources
            }
        response.append({
            "id": t.id,
            "user_id": t.user_id,
            "message": t.message,
            "decision": decision_dict
        })
    return response

@app.get("/tickets/{id}", response_model=TicketResponse)
async def read_ticket(id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.id == id, Ticket.user_id == current_user.id))
    ticket = result.scalars().first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or you don't have access")
        
    d_result = await db.execute(select(Decision).where(Decision.ticket_id == ticket.id))
    decision = d_result.scalars().first()
    decision_dict = None
    if decision:
        decision_dict = {
            "action": decision.action,
            "reason": decision.reason,
            "confidence": decision.confidence,
            "sources": decision.sources
        }
        
    return {
        "id": ticket.id,
        "user_id": ticket.user_id,
        "message": ticket.message,
        "decision": decision_dict
    }
