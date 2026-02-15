from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base

# database url
# This tells SQLAlchemy to create a file named "leetcode.db" in your current folder.
SQLALCHEMY_DATABASE_URL="sqlite:///./leetcode.db"

# The engine
# check_same_thread=False is a special requirement only for SQLite + FastAPI
engine=create_engine(SQLALCHEMY_DATABASE_URL,connect_args={"check_same_thread":False})

# The session
# This is what we will use to actually query the database (e.g., db.query(Problem))
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

# The Base Class
# All our database tables will inherit from this class
Base= declarative_base()