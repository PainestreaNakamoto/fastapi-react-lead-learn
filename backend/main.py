from typing import List
from fastapi import Depends, HTTPException, security , FastAPI
from fastapi.middleware.cors import CORSMiddleware
from requests import Session
import sqlalchemy.orm as _orm
# from backend.services import get_db
import services ,schemas

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/users")
async def create_user(user: schemas.UserCreate, db: _orm.Session = Depends(services.get_db)):
    db_user = await services.get_user_by_email( user.email, db )
    print(55)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already in use")
    
    return await services.create_user(user,db)

    # return await services.create_token(user)


@app.post("/api/token")
async def generate_token(form_data: security.OAuth2PasswordRequestForm = Depends(), db: _orm.Session = Depends(services.get_db)):
    user = await services.authenticate_user(form_data.username , form_data.password , db)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
    return await services.create_token(user)


@app.get("/api/users/me", response_model=schemas.User)
async def get_user(user: schemas.User = Depends(services.get_current_user)):
    return user


@app.get("/api/leads", response_model=List[schemas.Lead])
async def get_leads(user: schemas.User = Depends(services.get_current_user),db: Session = Depends(services.get_db)):
    return await services.get_leads(user, db)

@app.get('/api/leads/{id}', status_code=200)
async def get_lead_by_id(id: int, user: schemas.User = Depends(services.get_current_user), db: Session = Depends(services.get_db)):
    return await services.get_lead(id,user,db)

@app.post("/api/leads", response_model=schemas.Lead)
async def create_leads(lead: schemas.LeadCreate, user: schemas.User = Depends(services.get_current_user), db: Session = Depends(services.get_db)):
    return await services.create_leads(user=user, db=db, lead=lead)


@app.put("/api/leads/{id}", status_code=200)
async def update_lead(id: int, lead: schemas.LeadCreate ,user: schemas.User = Depends(services.get_current_user),db: Session = Depends(services.get_db)):
    await services.update_lead(id, lead, user, db)
    return {"message", "Successfully Updated"}

@app.delete("/api/leads/{id}", status_code=200)
async def delete_lead(id: int, user: schemas.User = Depends(services.get_current_user),db: Session = Depends(services.get_db)):
    await services.delete_lead(id,user,db) 
    return {'message': "Successfully Deleted"}

@app.get("/api")
async def root():
    return {"message": "Awesome Leads Manager"}