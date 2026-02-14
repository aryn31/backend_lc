from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
import docker
import os

app=FastAPI()

#connext to local docker desktop
client=docker.from_env()

class CodeSubmission(BaseModel):
    code: str #the python code user wants to run

@app.post("/execute")
def execute_code(submission: CodeSubmission):
    try:
        # 1. Create the container (The Prison Cell)
        # We mount nothing. The container is empty.
        # We inject the code directly as a command.
        
        # 'network_disabled=True' is CRITICAL. 
        # It stops the user from downloading malware or attacking your network.
        container=client.containers.run(
            "python-sandbox",   #the image we built
            command=["python","-c",submission.code], #run their code
            mem_limit="128m",    #max 128mb ram
            cpu_quota=50000,    #max 50% of 1 cpu core
            network_disabled=True,   #no internet access
            detach=True,    #run in bg
            auto_remove=True, #Automatically delete the container when it stops
            stdout=True,
            stderr=True
        )

        # 2. Wait for it to finish (The Timeout)
        # If code runs longer than 2 seconds, we kill it.

        try:
            container.wait(timeout=2)

            #3 capture the output (what did they print)
            logs=container.logs().decode("utf-8")

        except Exception as e:
            #if it is times out, kill the container manually
            container.kill()
            return {"status": "Error", "output": "Time Limit Exceeded (2s)"}

        #cleanup (destroy the cell)
        container.remove()

        return {"status": "Success", "output": logs}
    
    except Exception as e:
        return {"status":"System Error","details":str(e)}
    

@app.get("/")
def read_root():
    return {"status": "Judge System Online 👨‍⚖️"}
