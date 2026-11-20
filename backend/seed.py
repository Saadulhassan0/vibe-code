from .database import get_connection, now_utc

STARTER_FAQS = [
    ("FAQ-01", "Labs",
     "When is CS-LAB-102A open, and can I eat there?",
     "CS-LAB-102A is open from 08:00 AM to 06:00 PM, Monday to Friday. Food and drinks are not allowed inside the lab."),
    ("FAQ-02", "Academics",
     "What is the attendance requirement?",
     "Students need at least 80% attendance in each course. A student below 80% cannot sit the final exam of that course."),
    ("FAQ-03", "Library",
     "What are the library timings?",
     "The library is open from 08:30 AM to 08:00 PM, Monday to Thursday, and from 08:30 AM to 12:30 PM on Friday. It is closed on weekends."),
    ("FAQ-04", "Exams",
     "What if I miss a midterm because I was ill?",
     "Apply for a retake to the Course Coordinator within 3 working days of the exam, with a medical certificate."),
    ("FAQ-05", "Fees",
     "When is the Spring 2027 fee due?",
     "Download the fee challan from the student portal. The last date to pay without a fine is 15-Jan-2027."),
    ("FAQ-06", "FYP",
     "How do I submit my FYP proposal?",
     "Submit the Final Year Project proposal on SLATE by 30-Nov-2026. Each FYP group has 2 or 3 members."),
    ("FAQ-07", "Transport",
     "When do the university buses leave?",
     "University buses leave the campus at 01:30 PM and 04:30 PM, Monday to Friday. Bus cards are issued by the Transport Office in Block A."),
    ("FAQ-08", "Help",
     "Who do I contact for anything else?",
     "Email helpdesk@se.example.edu or visit Room 210, 09:00 AM to 04:00 PM, Monday to Friday.")
]

def seed_faqs():
    with get_connection() as conn:
        for code, category, question, answer in STARTER_FAQS:
            conn.execute(
                "INSERT OR IGNORE INTO categories(category_name) VALUES (?)",
                (category,)
            )
            category_id = conn.execute(
                "SELECT category_id FROM categories WHERE category_name=?",
                (category,)
            ).fetchone()["category_id"]
            conn.execute(
                """INSERT OR IGNORE INTO faqs
                   (faq_code, category_id, question, answer, is_active, created_at)
                   VALUES (?, ?, ?, ?, 1, ?)""",
                (code, category_id, question, answer, now_utc())
            )
