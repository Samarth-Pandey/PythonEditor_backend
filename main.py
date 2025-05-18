from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import re
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/execute")
async def execute_code(request: Request):
    data = await request.json()
    code = data.get("code")
    inputs: List[str] = data.get("inputs", [])
    
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")
    
   
    input_count = code.count("input(")
    
    
    if len(inputs) < input_count:
        input_matches = re.finditer(r'input\(([^)]*)\)', code)
        next_prompt = None
        for i, match in enumerate(input_matches):
            if i == len(inputs):
                next_prompt = match.group(1).strip('\"\'')
                break
        
        return {
            "status": "input_required",
            "prompt": next_prompt,
            "received_inputs": inputs
        }
    
    
    with open("temp.py", "w") as f:
        f.write(code)
    
    try:
       
        process = subprocess.Popen(
            ["python", "temp.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
       
        input_str = "\n".join(inputs) + "\n"
        
        
        stdout, stderr = process.communicate(input=input_str, timeout=10)
        
        output = stdout
        if stderr:
            output += f"\nERROR: {stderr}"
            
        return {
            "status": "completed",
            "output": output,
            "received_inputs": inputs
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "output": "ERROR: Execution timed out (max 10 seconds)"
        }
    except Exception as e:
        return {
            "status": "error",
            "output": f"ERROR: {str(e)}"
        }
    finally:
        if os.path.exists("temp.py"):
            os.remove("temp.py")