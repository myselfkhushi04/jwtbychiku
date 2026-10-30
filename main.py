from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Garena India Token API",
    version="3.1",
    description="API to generate guest/UID tokens for Free Fire India."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Garena India Auth Endpoint (Aap ise apne zaroorat ke hisaab se guest:token:grant ya login par set kar sakte hain)
TARGET_URL = "https://100067.connect.garena.com/api/v2/oauth/token:grant"

class LoginPayload(BaseModel):
    uid: str
    password: str

@app.get("/")
def home():
    return {
        "status": "Active",
        "message": "Garena India Token API is running on Vercel! 🚀",
        "region": "IND"
    }

@app.post("/get-token")
async def generate_token(data: LoginPayload):
    # Free Fire India / Android ke exact headers taaki server block na kare
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; SM-A205F Build/QP1A.190711.020)",
        "Content-Type": "application/json",
        "X-GA-Channel": "googleplay",
        "X-GA-Region": "IND",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "Keep-Alive"
    }

    request_body = {
        "uid": data.uid,
        "password": data.password,
        "region": "IND"
    }

    timeout_config = httpx.Timeout(20.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout_config) as client:
        try:
            logger.info(f"Processing India region request for UID: {data.uid}")
            
            response = await client.post(TARGET_URL, headers=headers, json=request_body)
            
            if response.status_code == 200:
                try:
                    res_data = response.json()
                    return {
                        "success": True,
                        "status_code": 200,
                        "data": res_data
                    }
                except Exception:
                    return {
                        "success": True,
                        "status_code": 200,
                        "raw_response": response.text
                    }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error_message": response.text
                }
                
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Gateway Timeout: Garena server took too long to respond.")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Bad Gateway: Connection failed. Error: {str(exc)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
