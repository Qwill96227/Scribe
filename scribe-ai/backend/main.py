from fastapi import FastAPI, Body, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from file_handling import upload_multimedia_file
from firebase_admin import credentials, initialize_app
from firebase_admin import firestore
from firebase_admin import auth
from jose import jwt
import asyncio
from concurrent.futures import ThreadPoolExecutor
from async_utils import run_async_firebase_op
from fastapi import Request
from fastapi import HTTPException


# Initialize the Firebase Admin SDK
cred = credentials.Certificate(r'C:\Users\qwill\Downloads\scribe-ai-fe9d2-firebase-adminsdk-gnevq-ee66973f53.json')
firebase_admin.initialize_app(cred, {
    'projectId': 'scribe-ai-fe9d2',
})

db = firestore.client()

app = FastAPI()

# CORS Middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_file(file: UploadFile = None, model_type: str = None):
    if not file:
        raise HTTPException(status_code=422, detail="File is required")
    if not model_type:
        raise HTTPException(status_code=422, detail="Model type is required")

    transcript = await upload_multimedia_file(file, model_type)
    return {"status": "success", "transcript": transcript}



@app.get("/")
async def root():
    return {"message": "Welcome to ScribeAI Backend"}

@app.post("/signup")
async def signup(request: Request):
    try:
        data = await request.json()
        id_token = data.get("id_token")
        
        if not id_token:
            return {"error": "Missing id_token"}

        # Verify ID token using async-friendly approach
        decoded_token = await run_async_firebase_op(auth.verify_id_token, id_token)
        user_uid = decoded_token["user_id"]

        # Create user in Firestore using async-friendly approach
        user_data = {
            "username": data.get("username"),
            "email": data.get("email"),
            "uid": user_uid
        }
        await run_async_firebase_op(
            db.collection("users").document(user_uid).set, 
            user_data
        )

        return {"message": "User registered successfully"}
    except Exception as e:
        print(f"Signup error: {e}")  # Log the actual error
        return {"error": str(e)}

@app.get("/users/{uid}")
async def get_user(uid: str):
    try:
        # Retrieve user data from Firestore using async-friendly approach
        doc = await run_async_firebase_op(
            db.collection('users').document(uid).get
        )
        
        if doc.exists:
            return doc.to_dict()
        else:
            return {"error": "User not found"}
    except Exception as e:
        print(f"Get user error: {e}")  # Log the actual error
        return {"error": str(e)}