# -*- coding: utf-8 -*-
import os
from datetime import datetime

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# ----------------------------------------------------------------------
# Database setup
# ----------------------------------------------------------------------
DATABASE_URL = "sqlite:///./contacts.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------------------------------------------------------------
# FastAPI app
# ----------------------------------------------------------------------
app = FastAPI()


@app.on_event("startup")
def startup_event():
    init_db()


# ----------------------------------------------------------------------
# Helper: static services list
# ----------------------------------------------------------------------
SERVICES = [
    {"name": "Haircut", "price": "$30"},
    {"name": "Hair Coloring", "price": "$70"},
    {"name": "Styling", "price": "$45"},
    {"name": "Shampoo & Blowdry", "price": "$25"},
]


# ----------------------------------------------------------------------
# Root page – shows services, contact form, contacts table and total
# ----------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    # Fetch contacts from DB
    db: Session = next(get_db())
    contacts = db.query(Contact).order_by(Contact.created_at.desc()).all()
    total_contacts = len(contacts)

    # Build HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hair Salon</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin:0; padding:0; background:#f4f4f4; }}
            .container {{ max-width: 900px; margin: auto; padding: 20px; background:#fff; }}
            h1, h2 {{ text-align: center; color:#333; }}
            .services {{ display:flex; flex-wrap:wrap; justify-content:space-around; margin-bottom:30px; }}
            .service-item {{ flex:1 1 200px; background:#e2e2e2; margin:10px; padding:15px; border-radius:8px; text-align:center; }}
            form {{ display:flex; flex-direction:column; gap:10px; }}
            input, textarea {{ padding:8px; border:1px solid #ccc; border-radius:4px; width:100%; }}
            button {{ padding:10px; background:#28a745; color:#fff; border:none; border-radius:4px; cursor:pointer; }}
            button:hover {{ background:#218838; }}
            table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
            th, td {{ border:1px solid #ddd; padding:8px; text-align:left; }}
            th {{ background:#f2f2f2; }}
            @media (max-width:600px) {{
                .services {{ flex-direction:column; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to Our Hair Salon</h1>

            <h2>Our Services</h2>
            <div class="services">
    """
    for svc in SERVICES:
        html_content += f"""
                <div class="service-item">
                    <strong>{svc['name']}</strong><br>
                    {svc['price']}
                </div>
        """
    html_content += """
            </div>

            <h2>Contact Us</h2>
            <form action="/contact" method="post">
                <input type="text" name="name" placeholder="Your Name" required>
                <input type="email" name="email" placeholder="Your Email" required>
                <input type="text" name="phone" placeholder="Phone Number" required>
                <textarea name="message" placeholder="Your Message" rows="4" required></textarea>
                <button type="submit">Send Message</button>
            </form>

            <h2>Messages Received ({total_contacts})</h2>
            <table>
                <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Message</th>
                    <th>Date</th>
                </tr>
    """
    for idx, contact in enumerate(contacts, start=1):
        html_content += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{contact.name}</td>
                    <td>{contact.email}</td>
                    <td>{contact.phone}</td>
                    <td>{contact.message}</td>
                    <td>{contact.created_at.strftime('%Y-%m-%d %H:%M')}</td>
                </tr>
        """
    html_content += """
            </table>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ----------------------------------------------------------------------
# Contact form handler – saves data and redirects back to root
# ----------------------------------------------------------------------
@app.post("/contact")
def submit_contact(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    message: str = Form(...),
):
    db: Session = next(get_db())
    new_contact = Contact(name=name, email=email, phone=phone, message=message)
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return RedirectResponse(url="/", status_code=303)


# ----------------------------------------------------------------------
# Run with uvicorn (Render will use this entrypoint)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import os, uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))