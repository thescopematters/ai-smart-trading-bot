import os
from dotenv import load_dotenv
from database import Base, engine, SessionLocal, User, DefaultQuestion
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
        admin_email = os.getenv("ADMIN_EMAIL")
        
        existing_admin = db.query(User).filter(User.username == admin_user).first()
        if not existing_admin:
            print(f"Seeding admin user: {admin_user}")
            admin = User(
                email=admin_email,
                username=admin_user,
                password_hash=get_password_hash(admin_pass),
                display_name="System Admin",
                role="admin",
                is_guest=False
            )
            db.add(admin)
            db.commit()
        else:
            print("Admin user already exists.")

        # Seed guest user if empty
        existing_guest = db.query(User).filter(User.id == "guest").first()
        if not existing_guest:
            print("Seeding guest user...")
            guest = User(
                id="guest",
                username="guest_user",
                display_name="Guest User",
                role="user",
                is_guest=True
            )
            db.add(guest)
            db.commit()

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
        from database import Coin, PaperWallet, Balance
        if db.query(Coin).count() == 0:
            print("Seeding initial coins...")
            btc = Coin(name="Bitcoin", symbol="BTC", price="65000.00")
            eth = Coin(name="Ethereum", symbol="ETH", price="3500.00")
            db.add_all([btc, eth])
            db.commit()

            # Give Guest some initial money
            if not db.query(PaperWallet).filter(PaperWallet.user_id == "guest").first():
                wallet = PaperWallet(user_id="guest", cash_balance="100000.00", initial_balance="100000.00")
                db.add(wallet)
                # Give some initial BTC balance
                bal = Balance(user_id="guest", coin_id=btc.id, balance="1.5")
                db.add(bal)
                db.commit()
        
        print("Database setup complete.")
    finally:
        db.close()

if __name__ == "__main__":
    setup_database()
