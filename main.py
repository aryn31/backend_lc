from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from typing import List,Any
import tempfile
import json
import docker
import os

app=FastAPI()

#connext to local docker desktop
client=docker.from_env()

# --- data models ---
class TestCase(BaseModel):
    inputs: List[Any]
    expected: Any

class CodeSubmission(BaseModel):
    code: str #the python code user wants to run
    function_name: str
    test_cases: List[TestCase]

# --- Wrapper script generator ---

def generate_test_script(user_code: str,function_name: str,test_cases: List[TestCase]) -> str:
    test_cases_json=json.dumps([tc.model_dump() for tc in test_cases])

    wrapper_code= f"""import json
import sys

# --- USER CODE ---
{user_code}

def write_output(data):
    with open('/app/output.json','w') as f:
        json.dump(data,f)

if __name__ == "__main__":
    test_cases = json.loads('''{test_cases_json}''')
    passed_count=0

    for i,tc in enumerate(test_cases):
        inputs=tc["inputs"]
        expected=tc["expected"]

        try:
            result = {function_name}(*inputs)
            if result == expected:
                passed_count+=1
            else:
                write_output({{"status": "Failed", "test_case": i + 1, "expected": expected, "got": result}})
                sys.exit(0)

        except Exception as e:
            write_output({{"status": "Error", "test_case": i + 1, "error": str(e)}})
            sys.exit(0)
            
    write_output({{"status": "Accepted", "passed": passed_count, "total": len(test_cases)}})
"""
    return wrapper_code

# --- 3. The Bulletproof Execution Endpoint ---
@app.post("/submit")
def submit_code(submission: CodeSubmission):
    final_script = generate_test_script(
        user_code=submission.code,
        function_name=submission.function_name,
        test_cases=submission.test_cases
    )
    
    # FIX 1: Use your current project folder instead of Mac's weird /tmp folder
    current_dir = os.getcwd() 
    with tempfile.TemporaryDirectory(dir=current_dir) as temp_dir:
        runner_path = os.path.join(temp_dir, "runner.py")
        output_path = os.path.join(temp_dir, "output.json")
        
        with open(runner_path, "w") as f:
            f.write(final_script)
            
        try:
            container = client.containers.run(
                "python-sandbox", 
                command=["python", "/app/runner.py"],
                volumes={
                    # Explicitly use absolute path for Mac compatibility
                    os.path.abspath(temp_dir): {'bind': '/app', 'mode': 'rw'}
                },
                detach=True,
                # FIX 2: Temporarily disable auto_remove so we can read the crime scene logs
                auto_remove=False,  
                mem_limit="128m",
                cpu_quota=50000,
                network_disabled=True
            )
            
            try:
                container.wait(timeout=2)
            except Exception:
                container.kill()
                container.remove() # Manually clean up
                return {"status": "Time Limit Exceeded"}
                
            # FIX 3: If output.json is missing, grab the actual Docker logs!
            if os.path.exists(output_path):
                with open(output_path, "r") as f:
                    result = json.load(f)
                container.remove() # Manually clean up
                return result
            else:
                # Grab the logs to see the exact Python error
                error_logs = container.logs().decode("utf-8")
                container.remove() # Manually clean up
                return {
                    "status": "Container Crashed", 
                    "docker_logs": error_logs,
                    "hint": "Read the docker_logs above. It will tell you the exact Python error!"
                }

        except Exception as e:
            return {"status": "System Error", "details": str(e)}
        

@app.get("/")
def read_root():
    return {"status": "Judge System Online 👨‍⚖️"}
