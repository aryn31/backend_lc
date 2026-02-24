from fastapi import FastAPI,HTTPException,Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List,Any
import tempfile
import json
import docker
import os

from database import SessionLocal
from models import Problem,TestCase,Submission

from fastapi.middleware.cors import CORSMiddleware 

app=FastAPI()

# --- 2. ADD THIS ENTIRE BLOCK IMMEDIATELY AFTER app = FastAPI() ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your React app (port 5173) to connect
    allow_credentials=True,
    allow_methods=["*"],  # This tells FastAPI to accept the "OPTIONS" request!
    allow_headers=["*"],
)


#connext to local docker desktop
client=docker.from_env()

# 1- database dependency
def getdb():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()



# --- new data models ---
class CodeSubmission(BaseModel):
    problem_id: int
    language: str # python or cpp
    code: str #the python code user wants to run

# --- Wrapper script generator ---

def generate_test_script(user_code: str,function_name: str,test_cases: list) -> str:
    test_cases_json=json.dumps(test_cases)

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
                write_output({{"status": "Failed", "test_case": i + 1, "inputs": inputs,"expected": expected, "got": result}})
                sys.exit(0)

        except Exception as e:
            write_output({{"status": "Error", "test_case": i + 1, "error": str(e)}})
            sys.exit(0)
            
    write_output({{"status": "Accepted", "passed": passed_count, "total": len(test_cases)}})
"""
    return wrapper_code

def generate_cpp_script(user_code: str, function_name: str, test_cases: list) -> str:
    cpp_code = f"""#include <iostream>
#include <fstream>
#include <string>

// --- USER CODE ---
{user_code}

int main() {{
    std::ofstream out("/app/output.json");
    int passed_count = 0;
"""
    for i, tc in enumerate(test_cases):
        inputs = ", ".join(map(str, tc["inputs"])) 
        expected = tc["expected"]

        inputs_display=f"[{inputs}]"
        
        # FIX: We now evaluate the function FIRST and store it in 'result_i'.
        # This prevents the C++ stream from breaking our JSON string!
        cpp_code += f"""
    int result_{i} = {function_name}({inputs});
    
    if (result_{i} == {expected}) {{
        passed_count++;
    }} else {{
        // adding new inputs field in json string
        out << "{{\\"status\\": \\"Failed\\", \\"test_case\\": {i+1},\\"input\\":{inputs_display}, \\"expected\\": {expected}, \\"got\\": " << result_{i} << "}}";
        return 0;
    }}
"""
    cpp_code += f"""
    out << "{{\\"status\\": \\"Accepted\\", \\"passed\\": " << passed_count << ", \\"total\\": {len(test_cases)}}}";
    return 0;
}}
"""
    return cpp_code

# --- 3. The Bulletproof Execution Endpoint ---
@app.post("/submit")
def submit_code(submission: CodeSubmission,db: Session=Depends(getdb)):

    # 1 - fetch problem from database
    problem=db.query(Problem).filter(Problem.id==submission.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404,detail="Problem not found!")

    # 2 - fetch all test cases for this problem (including the hidden ones)
    db_testcases=db.query(TestCase).filter(TestCase.problem_id==submission.problem_id).all()

    # format them for our script generator
    formatted_test_cases=[
        {"inputs":tc.inputs, "expected":tc.expected_output}
        for tc in db_testcases
    ]

    # 3 - generate the script
    # final_script = generate_test_script(
    #     user_code=submission.code,
    #     function_name=problem.function_name, # pulled from db
    #     test_cases=formatted_test_cases # pulled from db
    # )
    # 4 - run docker execution

    # FIX 1: Use your current project folder instead of Mac's weird /tmp folder
    current_dir = os.getcwd()
    result=None

    with tempfile.TemporaryDirectory(dir=current_dir) as temp_dir:
        output_path = os.path.join(temp_dir, "output.json")

        if(submission.language=="python"):
            runner_path = os.path.join(temp_dir, "runner.py")
            final_script=generate_test_script(submission.code,problem.function_name,formatted_test_cases)
            with open(runner_path,"w") as f:
                f.write(final_script)

            docker_image="python-sandbox"
            # command jjust run the python file
            docker_command=["python","/app/runner.py"]

        elif submission.language=="cpp":
            runner_path = os.path.join(temp_dir, "runner.cpp")
            final_script = generate_cpp_script(submission.code, problem.function_name, formatted_test_cases)
            with open(runner_path, "w") as f:
                f.write(final_script)
                
            docker_image = "cpp-sandbox"
            # Command: Compile  the code FIRST, and if successful (&&), run the compiled binary

            docker_command=["sh","-c","g++ /app/runner.cpp -o /app/run && /app/run"]

        else:
            return {"status":"Error","details":"unsupported language"}

        #run docker execution
        
        try:
            container = client.containers.run(
                docker_image, 
                docker_command,
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
                

            if not result:
                if os.path.exists(output_path):
                    with open(output_path, "r") as f:
                        result = json.load(f)
                    container.remove()
                else:
                    error_logs = container.logs().decode("utf-8")
                    container.remove()
                    result = {
                        "status": "Container Crashed", 
                        "docker_logs": error_logs,
                    }

        except Exception as e:
            return {"status": "System Error", "details": str(e)}
        
    # 5 - save submission history to the db
    new_submission=Submission(
        problem_id=problem.id,
        user_code=submission.code,
        status=result.get("status","Unknown")

    )
    db.add(new_submission)
    db.commit()
    return result

@app.get("/")
def read_root():
    return {"status": "Judge System Online 👨‍⚖️"}
# --- 5. NEW: See all problems ---
@app.get("/problems")
def get_problems(db: Session=Depends(getdb)):
    problems = db.query(Problem).all()
    return [{"id": p.id, "title": p.title, "difficulty": p.difficulty} for p in problems]

@app.get("/problems/{problem_id}/submissions")
def get_submissions(problem_id:int, db: Session=Depends(getdb)):
    #fetch all the submissions for this problem ordered by newest first (.desc())
    submissions=db.query(Submission).filter(Submission.problem_id==problem_id).order_by(Submission.id.desc()).all()

    #format the data to send back to react
    return [
        {
            "id" : sub.id,
            "status" : sub.status,
            "code" : sub.user_code
        }
        for sub in submissions
    ]