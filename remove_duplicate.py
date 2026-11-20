
from app.database import get_connection

duplicate_ids = (
    "FAQ-09",
    "FAQ-18",
    "FAQ-75",
    "FAQ-76"
)

with get_connection() as conn:

    for faq_id in duplicate_ids:

        conn.execute(
            """
            UPDATE faqs
            SET is_active = 0
            WHERE faq_code = ?
            """,
            (faq_id,)
        )

    conn.commit()

print("Duplicate FAQs deactivated successfully.")
