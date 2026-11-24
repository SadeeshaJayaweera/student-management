"""
scripts/seed_demo_telemetry.py
Populates demo athletics, campus operations, hostel rooms, shuttle routes, invoices, and MCP logs
so all views in NSBM EduSphere render realistic, production-level operational telemetry.
"""
import asyncio
from datetime import datetime, date, timedelta
from sqlalchemy import select, func
from backend.database import AsyncSessionLocal
from backend.models import (
    User,
    Student,
    HostelBuilding,
    HostelRoom,
    TransportVehicle,
    ShuttleRoute,
    ShuttleSchedule,
    StudentTransportPass,
    CampusFacility,
    StudentInvoice,
)

async def seed_more_telemetry():
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding hostel rooms, shuttle routes & invoices...")

        stu_res = await db.execute(select(Student).limit(10))
        students = stu_res.scalars().all()

        # 1. Hostel rooms
        res_rooms = await db.execute(select(func.count(HostelRoom.id)))
        if res_rooms.scalar() == 0:
            b_res = await db.execute(select(HostelBuilding))
            buildings = b_res.scalars().all()
            for b in buildings:
                for fl in range(1, 5):
                    for r in range(1, 6):
                        room = HostelRoom(
                            building_id=b.id,
                            room_number=f"{b.code[-2:]}-{fl}0{r}",
                            floor=fl,
                            room_type="double" if r % 2 == 0 else "single",
                            capacity=2 if r % 2 == 0 else 1,
                            occupied_count=2 if r % 2 == 0 else 1,
                            monthly_fee=18500.0 if r % 2 != 0 else 14500.0,
                            status="available" if r == 5 else "full",
                        )
                        db.add(room)

        # 2. Shuttle Routes & Schedules & Passes
        res_routes = await db.execute(select(func.count(ShuttleRoute.id)))
        if res_routes.scalar() == 0:
            r1 = ShuttleRoute(
                route_name="Colombo Fort - NSBM Green Express",
                route_code="SH-CMB-01",
                origin="Colombo Fort Railway Station",
                destination="NSBM Green University Complex",
                distance_km=28.5,
                estimated_duration_mins=45,
                fare_amount=200.0,
                is_active=True,
            )
            r2 = ShuttleRoute(
                route_name="Kaduwela / Malabe Academic Link",
                route_code="SH-KAD-02",
                origin="Kaduwela Clock Tower Junction",
                destination="NSBM Green University Complex",
                distance_km=14.0,
                estimated_duration_mins=25,
                fare_amount=120.0,
                is_active=True,
            )
            r3 = ShuttleRoute(
                route_name="Maharagama / Nugegoda Commuter",
                route_code="SH-MHR-03",
                origin="Maharagama Central Bus Terminal",
                destination="NSBM Green University Complex",
                distance_km=19.2,
                estimated_duration_mins=35,
                fare_amount=160.0,
                is_active=True,
            )
            db.add_all([r1, r2, r3])
            await db.flush()

            v_res = await db.execute(select(TransportVehicle).limit(3))
            vehicles = v_res.scalars().all()

            for i, r in enumerate([r1, r2, r3]):
                v_id = vehicles[i % len(vehicles)].id if vehicles else None
                s1 = ShuttleSchedule(
                    route_id=r.id,
                    vehicle_id=v_id,
                    departure_time="07:15",
                    arrival_time="08:00",
                    days_of_week=["monday", "tuesday", "wednesday", "thursday", "friday"],
                    shift_type="morning_inbound",
                    is_active=True,
                )
                s2 = ShuttleSchedule(
                    route_id=r.id,
                    vehicle_id=v_id,
                    departure_time="17:30",
                    arrival_time="18:15",
                    days_of_week=["monday", "tuesday", "wednesday", "thursday", "friday"],
                    shift_type="evening_outbound",
                    is_active=True,
                )
                db.add_all([s1, s2])

            for stu in students[:6]:
                p = StudentTransportPass(
                    student_id=stu.id,
                    route_id=r1.id,
                    pass_type="semester",
                    valid_from=date.today() - timedelta(days=30),
                    valid_until=date.today() + timedelta(days=90),
                    qr_code_token=f"PASS-QR-{stu.id}-2026",
                    fare_paid=14500.0,
                    status="active",
                )
                db.add(p)

        # 3. Student Invoices
        res_inv = await db.execute(select(func.count(StudentInvoice.id)))
        if res_inv.scalar() == 0:
            print("💳 Seeding Student Invoices...")
            for i, stu in enumerate(students):
                paid = 180000.0 if i < 8 else 90000.0
                total = 180000.0
                inv = StudentInvoice(
                    invoice_number=f"INV-2026-{1000 + i}",
                    student_id=stu.id,
                    academic_term="Year 3 Semester 1 (2026)",
                    total_amount=total,
                    discount_amount=0.0,
                    paid_amount=paid,
                    balance_due=total - paid,
                    currency="LKR",
                    issue_date=date.today() - timedelta(days=45),
                    due_date=date.today() + timedelta(days=15),
                    status="paid" if paid == total else "partially_paid",
                    payment_plan_type="full" if paid == total else "installment_2",
                )
                db.add(inv)

        await db.commit()
        print("✅ Completed extended telemetry seeding!")

if __name__ == "__main__":
    asyncio.run(seed_more_telemetry())
