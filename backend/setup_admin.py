import os
from dotenv import load_dotenv
from database import Base, engine, SessionLocal, AdminUser, DefaultQuestion
from auth import get_password_hash

load_dotenv()

def setup_database(): 
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if admin exists
        admin_user = os.getenv("ADMIN_USERNAME")
        admin_pass = os.getenv("ADMIN_PASSWORD")
        
        existing_admin = db.query(AdminUser).filter(AdminUser.username == admin_user).first()
        if not existing_admin:
            print(f"Seeding admin user: {admin_user}")
            admin = AdminUser(
                username=admin_user,
                password_hash=get_password_hash(admin_pass),
                display_name="System Admin"
            )
            db.add(admin)
            db.commit()
        else:
            print("Admin user already exists.")

        # Seed default questions if empty
        if db.query(DefaultQuestion).count() == 0:
            print("Seeding default questions...")
            questions = [
                "What is the current price of Bitcoin?",
                "Show me the latest crypto news.",
                "How does paper trading work?",
                "Which coins are trending today?",
                "Check my portfolio balance."
            ]
            for i, text in enumerate(questions):
                q = DefaultQuestion(question_text=text, display_order=i)
                db.add(q)
            db.commit()

        # --- Seed Trading Data (Optional) ---
        # Seed logic for users can be added here if needed in the future
        
        print("Database setup complete.")
        
        print("Database setup complete.")
    finally:
        db.close()

if __name__ == "__main__":
    setup_database()
