from datetime import datetime
from fastapi import Depends, HTTPException
from requests import Session
from database import SessionLocal
import database as _database , models as _models , schemas as _schemas
import sqlalchemy.orm as _orm
import passlib.hash as _hash
import jwt
from fastapi.security import OAuth2PasswordBearer

oauth2schemas = OAuth2PasswordBearer(tokenUrl="/api/token")

JWT_KEY = "akxnwwewaroieb3frkaras"

def create_database():
    return _models.Base.metadata.create_all(bind=_database.engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  

async def get_user_by_email(email: str, db: _orm.Session):
    return db.query(_models.User).filter(_models.User.email == email).first()

async def create_user(user: _schemas.UserCreate, db: _orm.Session):
    user_obj = _models.User(email=user.email , password= _hash.bcrypt.hash(user.hashed_password), username=user.username)
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj

async def authenticate_user(email: str, password: str, db: Session):
    user = await get_user_by_email(email,db)

    if not user:
        return False
    
    if not user.verify_password(password):
        return False

    return user

async def create_token(user: _models.User):
    user_obj = _schemas.User.from_orm(user)
    token = jwt.encode(user_obj.dict(),JWT_KEY)

    return dict(access_token=token, token_type="bearer")


async def get_current_user(db: Session = Depends(get_db),token: str = Depends(oauth2schemas)):
    try:
        payload = jwt.decode(token,JWT_KEY,algorithms=["HS256"])
        user = db.query(_models.User).get(payload["id"])
    except:
        raise HTTPException(status_code=401, detail="Invalid Email or password")
    
    return _schemas.User.from_orm(user)

async def create_leads(user: _schemas.User, db: Session, lead: _schemas.LeadCreate):
    lead = _models.Lead(**lead.dict(), owner_id=user.id)
    db.add(lead)
    db.commit()
    db.refresh(lead)

    return _schemas.Lead.from_orm(lead)

async def get_leads(user: _schemas.User, db: Session): 
    leads = db.query(_models.Lead).filter_by(owner_id=user.id)

    return list(map(_schemas.Lead.from_orm, leads))

async def lead_selector(lead_id: int ,user: _schemas.User, db: Session):
    lead = (db.query(_models.Lead)
        .filter_by(owner_id=user.id)
        .filter(_models.Lead.id == lead_id)
        .first()
        )
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead does not exit")
    
    return lead

async def get_lead(lead_id: int , user: _schemas.User, db: Session):
    lead = await lead_selector(lead_id=lead_id, user=user, db=db)

    return _schemas.Lead.from_orm(lead)


async def delete_lead(lead_id: int, user: _schemas.User, db: Session):
    lead = await lead_selector(lead_id, user, db)

    db.delete(lead)
    db.commit()

async def update_lead(lead_id: int, lead: _schemas.LeadCreate, user: _schemas.User, db: Session):
    lead_db = await lead_selector(lead_id, user, db)

    lead_db.first_name = lead.first_name
    lead_db.last_name = lead.last_name
    lead_db.email = lead.email
    lead_db.company = lead.company
    lead_db.note = lead.note
    lead_db.date_last_updated = datetime.utcnow()

    db.commit()
    db.refresh(lead_db)

    return _schemas.Lead.from_orm(lead_db)