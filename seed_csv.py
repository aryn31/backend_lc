import pandas as pd
import json
import re
from database import engine, SessionLocal, Base
from models import Problem, TestCase

def generate_function_name(title: str) -> str:
    """Converts 'Add Two Numbers' to 'add_two_numbers'"""
    # Remove special characters and replace spaces with underscores
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    return clean.strip().replace(" ", "_").lower()

def run_csv_seed():
    print("🔨 Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    print("📂 Loading questions_dataset.csv...")
    try:
        df = pd.read_csv("questions_dataset.csv")
    except FileNotFoundError:
        print("❌ Error: questions_dataset.csv file not found!")
        return
        
    print(f"🚀 Found {len(df)} problems. Beginning injection...")
    
    inserted_count = 0
    
    # Loop through every row in the CSV
    for index, row in df.iterrows():
        title = row['title']
        description = row['description']
        difficulty = row['difficulty_level']
        function_name = generate_function_name(title)
        
        # Check if problem already exists
        existing = db.query(Problem).filter(Problem.title == title).first()
        if existing:
            continue
            
        # --- NEW: Parse examples and constraints safely ---
        examples_data = json.loads(row['examples']) if pd.notna(row['examples']) else []
        constraints_data = json.loads(row['constraints']) if pd.notna(row['constraints']) else []
            
        # Create the Problem WITH the new data
        new_problem = Problem(
            title=title,
            description=description,
            difficulty=difficulty,
            function_name=function_name,
            examples=examples_data,        # <-- ADDED
            constraints=constraints_data   # <-- ADDED
        )
        db.add(new_problem)
        db.commit()      
        db.refresh(new_problem)
        
        # 3. Parse and Insert Test Cases
        try:
            # Parse the JSON string from the CSV
            test_cases_data = json.loads(row['test_cases'])
            test_cases_to_insert = []
            
            for i, tc in enumerate(test_cases_data):
                # The CSV has inputs as dicts like {"k": 1, "nums": [1,2,3]}.
                # Our sandbox expects a list like [1, [1,2,3]]. We extract the values.
                raw_input = tc.get("input", {})
                inputs_list = list(raw_input.values()) if isinstance(raw_input, dict) else [raw_input]
                
                # Check for output key (sometimes it's 'output', sometimes 'expected_output')
                expected = tc.get("expected_output", tc.get("output"))
                
                # Make the first 2 test cases public, the rest HIDDEN
                is_hidden = True if i >= 2 else False
                
                new_tc = TestCase(
                    problem_id=new_problem.id,
                    inputs=inputs_list,
                    expected_output=expected,
                    is_hidden=is_hidden
                )
                test_cases_to_insert.append(new_tc)
                
            db.add_all(test_cases_to_insert)
            db.commit()
            inserted_count += 1
            
            if inserted_count % 50 == 0:
                print(f"✅ Inserted {inserted_count} problems...")
                
        except Exception as e:
            print(f"⚠️ Error parsing test cases for '{title}': {str(e)}")
            db.rollback()

    print(f"🎉 Bulk seed complete! Successfully injected {inserted_count} new problems.")
    db.close()

if __name__ == "__main__":
    run_csv_seed()