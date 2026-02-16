from database import engine, SessionLocal, Base
from models import Problem, TestCase

# 1. Create the physical database file (leetcode.db) and all tables
print("🔨 Building database tables...")
Base.metadata.create_all(bind=engine)

# 2. Open a connection to the database
db = SessionLocal()

# 3. Check if the database is already seeded (to prevent duplicates)
if db.query(Problem).first() is None:
    print("🌱 Seeding the first problem...")
    
    # --- Create the Problem ---
    problem1 = Problem(
        title="Add Two Numbers",
        description="Given two numbers a and b, return their sum.",
        difficulty="Easy",
        function_name="add"
    )
    
    # Add it to the session and commit (save) it to the database
    db.add(problem1)
    db.commit()
    db.refresh(problem1) # This updates problem1 to get its new database ID (which will be 1)

    # --- Create the Test Cases ---
    print("🔒 Adding secret test cases...")
    
    # Test Case 1: Public (Users can see this as an example)
    tc1 = TestCase(
        problem_id=problem1.id,
        inputs=[1, 2],
        expected_output=3,
        is_hidden=False 
    )
    
    # Test Case 2: Public
    tc2 = TestCase(
        problem_id=problem1.id,
        inputs=[10, 20],
        expected_output=30,
        is_hidden=False
    )
    
    # Test Case 3: HIDDEN (The user will not see this one!)
    tc3 = TestCase(
        problem_id=problem1.id,
        inputs=[-5, 5],
        expected_output=0,
        is_hidden=True
    )

    # Save all test cases at once
    db.add_all([tc1, tc2, tc3])
    db.commit()
    
    print("✅ Database successfully seeded!")
else:
    print("⚠️ Database already contains data. Skipping seed.")

# Close the connection
db.close()