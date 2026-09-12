"""
Dashboard metrics - every number here is a direct COUNT/aggregate over the
existing tables (or the crm_log-derived handoffs view), never a placeholder
or estimated figure.
"""
from agent import db
from backend.services import handoffs_service


def get_analytics() -> dict:
    conn = db.get_connection()

    total_leads = conn.execute("SELECT COUNT(*) AS c FROM leads").fetchone()["c"]
    tier_rows = conn.execute(
        "SELECT tier, COUNT(*) AS c FROM leads WHERE tier IS NOT NULL GROUP BY tier"
    ).fetchall()
    tier_counts = {r["tier"]: r["c"] for r in tier_rows}

    total_bookings = conn.execute(
        "SELECT COUNT(*) AS c FROM bookings WHERE status = 'confirmed'"
    ).fetchone()["c"]
    total_tours = conn.execute("SELECT COUNT(*) AS c FROM tours").fetchone()["c"]

    completed_tours = conn.execute(
        "SELECT COUNT(*) AS c FROM tours WHERE status = 'completed'"
    ).fetchone()["c"]
    no_show_tours = conn.execute(
        "SELECT COUNT(*) AS c FROM tours WHERE status = 'no_show'"
    ).fetchone()["c"]

    utilization_rows = conn.execute(
        """SELECT w.id, w.name, w.city, w.workspace_type,
                  COUNT(b.booking_id) AS booking_count
           FROM workspaces w
           LEFT JOIN bookings b ON b.workspace_id = w.id AND b.status = 'confirmed'
           GROUP BY w.id
           HAVING booking_count > 0
           ORDER BY booking_count DESC
           LIMIT 10"""
    ).fetchall()
    workspace_utilization = [
        {
            "workspace_id": r["id"], "name": r["name"], "city": r["city"],
            "workspace_type": r["workspace_type"], "booking_count": r["booking_count"],
        }
        for r in utilization_rows
    ]

    conn.close()

    conversion_rate = round((total_bookings / total_leads) * 100, 1) if total_leads else 0.0
    tour_show_rate = (
        round((completed_tours / (completed_tours + no_show_tours)) * 100, 1)
        if (completed_tours + no_show_tours) else None
    )

    return {
        "total_leads": total_leads,
        "hot_leads": tier_counts.get("hot", 0),
        "warm_leads": tier_counts.get("warm", 0),
        "cold_leads": tier_counts.get("cold", 0),
        "total_bookings": total_bookings,
        "total_tours": total_tours,
        "pending_handoffs": handoffs_service.pending_count(),
        "conversion_rate": conversion_rate,
        "tour_show_rate": tour_show_rate,
        "workspace_utilization": workspace_utilization,
    }
