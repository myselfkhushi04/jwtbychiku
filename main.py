from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging

# Logging setup taaki bugs ya errors terminal/logs me dikhein
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chiku Advanced Guest Token API",
    version="2.0",
    description="Production-ready API for generating Chiku guest tokens securely."
)

# CORS Middleware (Taaki kisi bhi frontend/app se easily call ho sake)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TARGET_URL = "https://100067.connect.garena.com/api/v2/oauth/guest:token:grant"

# Optional: Agar aap apni API ko secure karna chahte hain toh yahan secret key daal sakte hain
API_SECRET_KEY = "my_secret_token_123"  // Isko apne hisaab se change kar sakte hain

def verify_api_key(x_api_key: str = Header(None)):
    # Agar aapko security nahi chahiye toh neeche ki 2 lines hata sakte hain
    if API_SECRET_KEY and x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid or Missing API Key ❌")
    return True

@app.get("/")
def home():
    return {
        "status": "Active",
        "message": "Chiku Advanced API is running smoothly on Vercel! 🚀",
        "endpoints": {
            "generate_token": "/get-token (POST/GET)"
        }
    }

@app.api_route("/get-token", methods=["GET", "POST"])
async def generate_guest_token(
    payload: dict = None, 
    authorized: bool = Depends(verify_api_key)
):
    """
    Advanced Token Generator with Error Handling, Timeouts, and Header Forwarding.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }

    # HttpX client with timeout and limits to prevent hanging
    timeout_config = httpx.Timeout(20.0, connect=10.0)
    
    async with httpx.AsyncClient(timeout=timeout_config) as client:
        try:
            logger.info("Attempting to fetch guest token from Chiku server...")
            
            # Agar user ne request me koi body/payload bheja hai toh usko forward karein, warna empty dict
            request_body = payload if payload else {}
            
            # Chiku server par request bhej rahe hain (POST request zyadatar auth endpoints ke liye hoti hai)
            response = await client.post(TARGET_URL, headers=headers, json=request_body)
            
            # Response status check karein
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info("Token successfully generated!")
                    return {
                        "success": True,
                        "status_code": 200,
                        "data": data
                    }
                except json.JSONDecodeError:
                    # Agar response JSON me na ho
                    return {
                        "success": True,
                        "status_code": 200,
                        "raw_response": response.text
                    }
            else:
                logger.warning(f"Chiku server returned error status: {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error_message": response.text
                }
                
        except httpx.TimeoutException:
            logger.error("Request timed out while connecting to Chiku server.")
            raise HTTPException(
                status_code=504, 
                detail="Gateway Timeout: Chiku server did not respond in time. Please try again."
            )
        except httpx.RequestError as exc:
            logger.error(f"Network error occurred: {str(exc)}")
            raise HTTPException(
                status_code=502, 
                detail=f"Bad Gateway: Failed to connect to Chiku server. Error: {str(exc)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Internal Server Error: {str(e)}"
            )
