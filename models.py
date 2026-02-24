from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class Problem(Base):
    __tablename__="problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)          # e.g., "Add Two Numbers"
    description = Column(Text)                  # e.g., "Given two numbers, return their sum."
    difficulty = Column(String)                 # e.g., "Easy", "Medium", "Hard"
    function_name = Column(String)              # e.g., "add"

    # --- WE ARE ADDING THESE TWO LINES ---
    examples = Column(JSON)      
    constraints = Column(JSON)

    # Relationships: This allows us to easily fetch all test cases for a problem
    # by just typing: `my_problem.test_cases`
    test_cases = relationship("TestCase", back_populates="problem")
    submissions = relationship("Submission", back_populates="problem")

class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id")) # Links to Problems table
    
    # We store the inputs/outputs as JSON arrays
    inputs = Column(JSON)             # e.g., [1, 2]
    expected_output = Column(JSON)    # e.g., 3
    is_hidden = Column(Boolean, default=False) 

    # Relationship back to the parent problem
    problem = relationship("Problem", back_populates="test_cases")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    user_code = Column(Text)          # The exact code they submitted
    status = Column(String)           # e.g., "Accepted", "Time Limit Exceeded"

    # Relationship back to the parent problem
    problem = relationship("Problem", back_populates="submissions")