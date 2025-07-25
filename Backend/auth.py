from fastapi import APIRouter, HTTPException, Response, status, Request, Depends
from passlib.hash import bcrypt
from bson import ObjectId
from schemas import UserCreate, UserLogin, UserOut
from jose import JWTError, jwt
import os
from utils import generate_token
from database import collection

router = APIRouter()

@router.post("/signup", response_model=UserOut)
async def signup(user: UserCreate, res: Response):
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing_user = collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = bcrypt.hash(user.password)

    new_user = {
        "fullName": user.fullName,
        "email": user.email,
        "password": hashed_pw
    }

    result = collection.insert_one(new_user)
    user_id = str(result.inserted_id)

    token = generate_token(user_id)
    res.set_cookie(key="jwt", value=token, httponly=True, secure=True, samesite="none", max_age=7*24*60*60)

    return {**new_user, "_id": user_id}

@router.post("/login", response_model=UserOut)
async def login(user: UserLogin, res: Response):
    db_user = collection.find_one({"email": user.email})
    if not db_user or not bcrypt.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="The credentials are wrong")

    token = generate_token(str(db_user["_id"]))
    res.set_cookie(key="jwt", value=token, httponly=True, secure=True, samesite="none", max_age=7*24*60*60)

    return {
        "_id": str(db_user["_id"]),
        "fullName": db_user["fullName"],
        "email": db_user["email"]
    }

@router.post("/logout")
async def logout(res: Response):
    res.delete_cookie("jwt")
    return {"message": "Logout successful"}

@router.get("/check-auth", response_model=UserOut)
async def check_auth(request: Request):
    token = request.cookies.get("jwt")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "_id": str(user["_id"]),
            "fullName": user["fullName"],
            "email": user["email"]
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid or expired")
    



'''
Things To Do
.post -> uploading resume and JD (doc GridFS) {NLP + GenAI}
.get(user.email)-> curr user uploaded resumes
.get(resume id)-> for specific resume report

2File
1 rotes
1 NLP genAI 
'''