from collections import defaultdict
from datetime import datetime, timedelta, date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from .. import models
from ..database import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total_customers = db.query(models.Customer).count()
    total_products = db.query(models.Product).count()
    open_statuses = [
        models.OrderStatus.received, models.OrderStatus.confirmed,
        models.OrderStatus.packing, models.OrderStatus.packed,
        models.OrderStatus.out_for_delivery,
    ]
    open_orders = db.query(models.Order).filter(models.Order.status.in_(open_statuses)).count()
    delivered_orders = db.query(models.Order).filter(models.Order.status == models.OrderStatus.delivered).count()
    cancelled_orders = db.query(models.Order).filter(models.Order.status == models.OrderStatus.cancelled).count()

    week_ago = datetime.utcnow() - timedelta(days=7)
    orders_this_week = db.query(models.Order).filter(models.Order.created_at >= week_ago).count()
    delivered_this_week = db.query(models.Order).filter(
        models.Order.status == models.OrderStatus.delivered,
        models.Order.updated_at >= week_ago,
    ).count()

    inv_rows = db.query(models.Inventory).all()
    low_stock_count = sum(1 for r in inv_rows if (r.qty_on_hand - r.qty_reserved) <= r.reorder_threshold)

    return {
        "total_customers": total_customers,
        "total_products": total_products,
        "open_orders": open_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
        "orders_this_week": orders_this_week,
        "delivered_this_week": delivered_this_week,
        "low_stock_items": low_stock_count,
    }


@router.get("/inventory")
def inventory_report(db: Session = Depends(get_db)):
    rows = db.query(models.Inventory).all()
    out = []
    total_value = 0.0
    for r in rows:
        available = r.qty_on_hand - r.qty_reserved
        value = (r.qty_on_hand * r.product.unit_price) if r.product.unit_price else None
        if value:
            total_value += value
        out.append({
            "product_id": r.product_id,
            "sku": r.product.sku,
            "name": r.product.name,
            "description": r.product.description,
            "category": r.product.category,
            "item_type": r.product.item_type.value,
            "barcode": r.product.barcode,
            "warehouse": r.warehouse,
            "aisle": r.aisle,
            "bin_column": r.bin_column,
            "location": r.location,
            "qty_on_hand": r.qty_on_hand,
            "qty_reserved": r.qty_reserved,
            "qty_available": available,
            "reorder_threshold": r.reorder_threshold,
            "low_stock": available <= r.reorder_threshold,
            "estimated_value": value,
        })
    out.sort(key=lambda x: x["qty_available"])
    return {
        "items": out,
        "low_stock_count": sum(1 for i in out if i["low_stock"]),
        "total_estimated_value": total_value or None,
    }


@router.get("/orders-by-status")
def orders_by_status(db: Session = Depends(get_db)):
    counts = defaultdict(int)
    for o in db.query(models.Order).all():
        counts[o.status.value] += 1
    return dict(counts)


@router.get("/order-cycle-time")
def order_cycle_time(db: Session = Depends(get_db)):
    """Average time (hours) spent transitioning between each status, and total received->delivered."""
    stage_order = ["received", "confirmed", "packing", "packed", "out_for_delivery", "delivered"]
    transition_durations = defaultdict(list)   # "received->confirmed" -> [hours,...]
    total_durations = []

    orders = db.query(models.Order).all()
    for order in orders:
        history = sorted(order.status_history, key=lambda h: h.changed_at)
        if not history:
            continue
        for i in range(len(history) - 1):
            a, b = history[i], history[i + 1]
            hours = (b.changed_at - a.changed_at).total_seconds() / 3600
            key = f"{a.status.value}->{b.status.value}"
            transition_durations[key].append(hours)
        if history[0].status.value == "received" and history[-1].status.value == "delivered":
            total_hours = (history[-1].changed_at - history[0].changed_at).total_seconds() / 3600
            total_durations.append(total_hours)

    avg_transitions = {
        k: round(sum(v) / len(v), 2) for k, v in transition_durations.items()
    }
    avg_total = round(sum(total_durations) / len(total_durations), 2) if total_durations else None

    return {
        "average_hours_per_transition": avg_transitions,
        "average_received_to_delivered_hours": avg_total,
        "completed_order_count": len(total_durations),
    }


@router.get("/customers/top")
def top_customers(limit: int = 10, db: Session = Depends(get_db)):
    customers = db.query(models.Customer).all()
    rows = []
    for c in customers:
        order_count = len(c.orders)
        total_cases = sum(i.qty_ordered for o in c.orders for i in o.items)
        if order_count == 0:
            continue
        rows.append({
            "customer_id": c.id,
            "customer": c.name,
            "company": c.company,
            "email": c.email,
            "order_count": order_count,
            "total_cases_ordered": total_cases,
            "last_order_at": max(o.created_at for o in c.orders).isoformat(),
        })
    rows.sort(key=lambda r: r["total_cases_ordered"], reverse=True)
    return rows[:limit]


@router.get("/shipping")
def shipping_report(db: Session = Depends(get_db)):
    shipments = db.query(models.Shipment).all()
    by_carrier = defaultdict(lambda: {"count": 0, "delivered": 0, "transit_hours": []})

    for s in shipments:
        bucket = by_carrier[s.carrier]
        bucket["count"] += 1
        if s.status == models.ShipmentStatus.delivered and s.shipped_at and s.delivered_at:
            bucket["delivered"] += 1
            hours = (s.delivered_at - s.shipped_at).total_seconds() / 3600
            bucket["transit_hours"].append(hours)

    result = []
    for carrier, data in by_carrier.items():
        avg_hours = round(sum(data["transit_hours"]) / len(data["transit_hours"]), 2) if data["transit_hours"] else None
        result.append({
            "carrier": carrier,
            "shipment_count": data["count"],
            "delivered_count": data["delivered"],
            "avg_transit_hours": avg_hours,
        })
    return result


@router.get("/packing-productivity")
def packing_productivity(db: Session = Depends(get_db)):
    records = db.query(models.PackingRecord).all()
    by_staff = defaultdict(lambda: {"orders_packed": 0, "boxes": 0, "hours": []})
    for r in records:
        bucket = by_staff[r.packed_by]
        bucket["orders_packed"] += 1
        bucket["boxes"] += r.boxes
        order = r.order
        if order and order.created_at:
            hours = (r.packed_at - order.created_at).total_seconds() / 3600
            if hours >= 0:
                bucket["hours"].append(hours)
    return [
        {
            "packed_by": staff,
            "orders_packed": data["orders_packed"],
            "boxes": data["boxes"],
            "avg_hours_to_pack": round(sum(data["hours"]) / len(data["hours"]), 2) if data["hours"] else None,
        }
        for staff, data in by_staff.items()
    ]


@router.get("/alerts")
def alerts(db: Session = Depends(get_db)):
    """Exceptions worth a manager/CEO's attention right now."""
    issues = []

    # Low stock
    inv_rows = db.query(models.Inventory).all()
    low_stock = [r for r in inv_rows if (r.qty_on_hand - r.qty_reserved) <= r.reorder_threshold]
    if low_stock:
        issues.append({
            "severity": "warning",
            "category": "inventory",
            "message": f"{len(low_stock)} product(s) at or below reorder threshold",
            "count": len(low_stock),
        })

    # Orders stuck in a non-terminal status for more than 48 hours with no progress
    stale_cutoff = datetime.utcnow() - timedelta(hours=48)
    stuck_orders = db.query(models.Order).filter(
        models.Order.status.notin_([models.OrderStatus.delivered, models.OrderStatus.cancelled]),
        models.Order.updated_at <= stale_cutoff,
    ).all()
    if stuck_orders:
        issues.append({
            "severity": "critical",
            "category": "orders",
            "message": f"{len(stuck_orders)} order(s) haven't moved in over 48 hours",
            "count": len(stuck_orders),
            "order_numbers": [o.order_number for o in stuck_orders],
        })

    # Packing assignments overdue (created more than 24h ago, not completed)
    assign_cutoff = datetime.utcnow() - timedelta(hours=24)
    overdue_assignments = db.query(models.PackingAssignment).filter(
        models.PackingAssignment.status.in_([models.AssignmentStatus.assigned, models.AssignmentStatus.in_progress]),
        models.PackingAssignment.created_at <= assign_cutoff,
    ).all()
    if overdue_assignments:
        issues.append({
            "severity": "warning",
            "category": "production",
            "message": f"{len(overdue_assignments)} packing assignment(s) open for over 24 hours",
            "count": len(overdue_assignments),
        })

    # Pallets sitting in "building" status for a long time (loaded but never shipped)
    pallet_cutoff = datetime.utcnow() - timedelta(hours=48)
    stale_pallets = db.query(models.Pallet).filter(
        models.Pallet.status != models.PalletStatus.shipped,
        models.Pallet.created_at <= pallet_cutoff,
    ).all()
    if stale_pallets:
        issues.append({
            "severity": "warning",
            "category": "shipping",
            "message": f"{len(stale_pallets)} pallet(s) not yet shipped after 48+ hours",
            "count": len(stale_pallets),
        })

    return {"issue_count": len(issues), "issues": issues}


@router.get("/business-performance")
def business_performance(months: int = 6, db: Session = Depends(get_db)):
    """
    Monthly business performance for the last N months.
    Returns revenue, cases shipped, order count, new customers, and returns
    per calendar month, plus MTD totals and MoM % changes.
    """
    now = datetime.utcnow()

    # Build list of month buckets: [{"year": 2026, "month": 2, "label": "Feb 2026"}, ...]
    buckets = []
    for i in range(months - 1, -1, -1):
        # Walk backwards from current month
        m = (now.month - i - 1) % 12 + 1
        y = now.year - ((now.month - i - 1) // 12)
        buckets.append({"year": y, "month": m, "label": f"{date(y, m, 1).strftime('%b %Y')}"})

    def month_window(year, month):
        """Return (start_dt, end_dt) for a given month."""
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        return start, end

    def order_revenue(order):
        """Sum revenue for one order using snapshot price then product price as fallback."""
        total = 0.0
        for item in order.items:
            price = item.unit_price_snapshot or (item.product.unit_price if item.product else None)
            if price:
                total += price * item.qty_ordered
        return total

    # Preload all delivered orders and their items
    delivered_orders = (
        db.query(models.Order)
        .filter(models.Order.status == models.OrderStatus.delivered)
        .all()
    )

    # Preload all customers
    all_customers = db.query(models.Customer).all()

    # Preload all returns
    all_returns = db.query(models.CustomerReturn).all()

    monthly = []
    ytd_revenue = 0.0
    ytd_cases = 0
    ytd_orders = 0
    ytd_customers = 0
    ytd_returns_qty = 0
    ytd_year = now.year

    for b in buckets:
        start, end = month_window(b["year"], b["month"])
        is_current = (b["year"] == now.year and b["month"] == now.month)

        # Revenue + cases + orders — from delivered orders created in this month
        month_orders = [o for o in delivered_orders if start <= o.created_at < end]
        revenue = sum(order_revenue(o) for o in month_orders)
        cases = sum(i.qty_ordered for o in month_orders for i in o.items)
        order_count = len(month_orders)

        # New customers created this month
        new_customers = sum(1 for c in all_customers if start <= c.created_at < end)

        # Returns logged this month
        month_returns = [r for r in all_returns if start <= r.created_at < end]
        returns_qty = sum(r.qty for r in month_returns)
        returns_count = len(month_returns)

        # YTD accumulation
        if b["year"] == ytd_year:
            ytd_revenue += revenue
            ytd_cases += cases
            ytd_orders += order_count
            ytd_customers += new_customers
            ytd_returns_qty += returns_qty

        monthly.append({
            "label": b["label"],
            "year": b["year"],
            "month": b["month"],
            "is_current_month": is_current,
            "revenue": round(revenue, 2),
            "cases_shipped": cases,
            "order_count": order_count,
            "new_customers": new_customers,
            "returns_qty": returns_qty,
            "returns_count": returns_count,
        })

    # MoM change helpers (compare last complete month to the one before it)
    def mom_pct(current_val, prev_val):
        if prev_val == 0:
            return None
        return round((current_val - prev_val) / prev_val * 100, 1)

    # Current month (last bucket) and previous month (second-to-last)
    cur = monthly[-1]
    prev = monthly[-2] if len(monthly) >= 2 else None

    # Top customers by revenue (all time, delivered orders)
    cust_revenue = defaultdict(float)
    cust_cases = defaultdict(int)
    cust_name = {}
    for o in delivered_orders:
        cust_revenue[o.customer_id] += order_revenue(o)
        cust_cases[o.customer_id] += sum(i.qty_ordered for i in o.items)
        cust_name[o.customer_id] = f"{o.customer.name}{(' — ' + o.customer.company) if o.customer.company else ''}"

    top_customers = sorted(
        [{"customer": cust_name[cid], "revenue": round(rev, 2), "cases": cust_cases[cid]}
         for cid, rev in cust_revenue.items()],
        key=lambda x: x["revenue"], reverse=True
    )[:8]

    return {
        "monthly": monthly,
        "current_month": {
            "label": cur["label"],
            "revenue": cur["revenue"],
            "cases_shipped": cur["cases_shipped"],
            "order_count": cur["order_count"],
            "new_customers": cur["new_customers"],
            "returns_qty": cur["returns_qty"],
            "returns_count": cur["returns_count"],
            "revenue_mom_pct": mom_pct(cur["revenue"], prev["revenue"]) if prev else None,
            "cases_mom_pct": mom_pct(cur["cases_shipped"], prev["cases_shipped"]) if prev else None,
            "customers_mom_pct": mom_pct(cur["new_customers"], prev["new_customers"]) if prev else None,
            "returns_mom_pct": mom_pct(cur["returns_qty"], prev["returns_qty"]) if prev else None,
        },
        "ytd": {
            "revenue": round(ytd_revenue, 2),
            "cases_shipped": ytd_cases,
            "order_count": ytd_orders,
            "new_customers": ytd_customers,
            "returns_qty": ytd_returns_qty,
        },
        "annual_target": 6_000_000,
        "top_customers": top_customers,
    }
