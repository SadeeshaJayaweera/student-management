"""backend/routers/campus_operations.py
Comprehensive Campus Operations Router (Stage 07 Capstone)
Provides centralized administrative command-and-control telemetry,
aggregating Finance, Digital & Physical Library, Athletics, Journalism,
Hostel Accommodation, Transport Transit, and Facilities Management.
"""

from datetime import datetime, date, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import (
    User,
    StudentInvoice,
    PaymentTransaction,
    Book,
    DigitalLibraryResource,
    BorrowRecord,
    AthleticTeam,
    AthleteProfile,
    SportsFixture,
    News,
    HostelRoom,
    HostelMaintenanceRequest,
    TransportVehicle,
    ShuttleRoute,
    ShuttleSchedule,
    StudentTransportPass,
    CampusFacility,
    FacilityReservation,
)
from backend.schemas import (
    CampusOperationsOverviewOut,
    CampusOperationsDomainFinance,
    CampusOperationsDomainLibrary,
    CampusOperationsDomainAthletics,
    CampusOperationsDomainMedia,
    CampusOperationsDomainAccommodation,
    CampusOperationsDomainTransport,
    CampusOperationsDomainFacilities,
    CampusOperationalAlertOut,
)
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/campus-operations", tags=["Comprehensive Campus Operations"])


@router.get("/overview", response_model=CampusOperationsOverviewOut)
async def get_campus_operations_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Executive cross-system command center metrics across university operations."""
    now = datetime.utcnow()
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())

    # 1. Finance Domain
    inv_res = await db.execute(select(func.sum(StudentInvoice.total_amount)))
    tot_invoiced = float(inv_res.scalar() or 0.0)

    paid_res = await db.execute(select(func.sum(StudentInvoice.paid_amount)))
    tot_collected = float(paid_res.scalar() or 0.0)

    bal_res = await db.execute(select(func.sum(StudentInvoice.balance_due)))
    outstanding = float(bal_res.scalar() or 0.0)

    collection_rate = round((tot_collected / tot_invoiced * 100), 1) if tot_invoiced > 0 else 0.0

    finance_domain = CampusOperationsDomainFinance(
        total_invoiced=tot_invoiced,
        total_collected=tot_collected,
        collection_rate=collection_rate,
        outstanding_balance=outstanding,
    )

    # 2. Library Domain
    dig_res = await db.execute(select(func.count(DigitalLibraryResource.id)))
    tot_dig = dig_res.scalar() or 0

    bk_res = await db.execute(select(func.count(Book.id)))
    tot_books = bk_res.scalar() or 0

    borr_res = await db.execute(
        select(func.count(BorrowRecord.id)).where(BorrowRecord.status == "borrowed")
    )
    act_borrowings = borr_res.scalar() or 0

    od_res = await db.execute(
        select(func.count(BorrowRecord.id)).where(
            and_(BorrowRecord.status == "borrowed", BorrowRecord.due_date < now)
        )
    )
    overdue_loans = od_res.scalar() or 0

    library_domain = CampusOperationsDomainLibrary(
        total_digital_resources=tot_dig,
        total_physical_books=tot_books,
        active_borrowings=act_borrowings,
        overdue_loans=overdue_loans,
    )

    # 3. Athletics Domain
    tm_res = await db.execute(select(func.count(AthleticTeam.id)).where(AthleticTeam.is_active == True))
    act_teams = tm_res.scalar() or 0

    ath_res = await db.execute(select(func.count(AthleteProfile.id)))
    tot_athletes = ath_res.scalar() or 0

    fix_res = await db.execute(
        select(func.count(SportsFixture.id)).where(SportsFixture.scheduled_time >= now)
    )
    up_fixtures = fix_res.scalar() or 0

    athletics_domain = CampusOperationsDomainAthletics(
        active_teams=act_teams,
        roster_athletes=tot_athletes,
        upcoming_fixtures=up_fixtures,
    )

    # 4. Media Domain
    news_res = await db.execute(
        select(
            func.count(News.id),
            func.sum(News.views),
            func.sum(News.likes_count),
        ).where(News.status == "published")
    )
    n_row = news_res.first()
    pub_news = n_row[0] or 0
    tot_views = int(n_row[1] or 0)
    tot_likes = int(n_row[2] or 0)

    media_domain = CampusOperationsDomainMedia(
        published_articles=pub_news,
        total_views=tot_views,
        total_likes=tot_likes,
    )

    # 5. Accommodation Domain
    hrm_res = await db.execute(
        select(
            func.sum(HostelRoom.capacity),
            func.sum(HostelRoom.occupied_count),
        )
    )
    hrm_row = hrm_res.first()
    tot_beds = int(hrm_row[0] or 0)
    occ_beds = int(hrm_row[1] or 0)
    avail_beds = max(0, tot_beds - occ_beds)
    occ_rate = round((occ_beds / tot_beds * 100), 1) if tot_beds > 0 else 0.0

    hmaint_res = await db.execute(
        select(func.count(HostelMaintenanceRequest.id)).where(
            HostelMaintenanceRequest.status.in_(["reported", "in_progress"])
        )
    )
    pending_repairs = hmaint_res.scalar() or 0

    accommodation_domain = CampusOperationsDomainAccommodation(
        total_capacity=tot_beds,
        occupied_beds=occ_beds,
        available_beds=avail_beds,
        occupancy_rate=occ_rate,
        pending_repairs=pending_repairs,
    )

    # 6. Transport Domain
    veh_res = await db.execute(
        select(func.count(TransportVehicle.id)).where(TransportVehicle.status == "active")
    )
    act_veh = veh_res.scalar() or 0

    rt_res = await db.execute(select(func.count(ShuttleRoute.id)).where(ShuttleRoute.is_active == True))
    act_routes = rt_res.scalar() or 0

    sch_res = await db.execute(select(func.count(ShuttleSchedule.id)).where(ShuttleSchedule.is_active == True))
    act_trips = sch_res.scalar() or 0

    pass_res = await db.execute(
        select(func.count(StudentTransportPass.id)).where(
            and_(StudentTransportPass.status == "active", StudentTransportPass.valid_until >= date.today())
        )
    )
    act_passes = pass_res.scalar() or 0

    transport_domain = CampusOperationsDomainTransport(
        fleet_vehicles=act_veh,
        active_routes=act_routes,
        daily_trips=act_trips,
        active_transit_passes=act_passes,
    )

    # 7. Facilities Domain
    fac_res = await db.execute(
        select(
            func.count(CampusFacility.id),
            func.sum(CampusFacility.capacity),
        ).where(CampusFacility.is_active == True)
    )
    fac_row = fac_res.first()
    tot_fac = fac_row[0] or 0
    tot_fac_cap = int(fac_row[1] or 0)

    fac_today_res = await db.execute(
        select(func.count(FacilityReservation.id)).where(
            and_(
                FacilityReservation.status == "confirmed",
                FacilityReservation.start_time >= today_start,
                FacilityReservation.start_time <= today_end,
            )
        )
    )
    res_today = fac_today_res.scalar() or 0

    fac_pend_res = await db.execute(
        select(func.count(FacilityReservation.id)).where(FacilityReservation.status == "pending")
    )
    pending_appr = fac_pend_res.scalar() or 0

    facilities_domain = CampusOperationsDomainFacilities(
        total_venues=tot_fac,
        combined_capacity=tot_fac_cap,
        reservations_today=res_today,
        pending_approvals=pending_appr,
    )

    return CampusOperationsOverviewOut(
        generated_at=now,
        institution_name="NSBM Green University",
        finance=finance_domain,
        library=library_domain,
        athletics=athletics_domain,
        media=media_domain,
        accommodation=accommodation_domain,
        transport=transport_domain,
        facilities=facilities_domain,
    )


@router.get("/alerts", response_model=List[CampusOperationalAlertOut])
async def get_campus_operational_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dynamic operational alerts across university infrastructure."""
    alerts = []
    now = datetime.utcnow()

    # Overdue library books check
    od_res = await db.execute(
        select(func.count(BorrowRecord.id)).where(
            and_(BorrowRecord.status == "borrowed", BorrowRecord.due_date < now)
        )
    )
    od_count = od_res.scalar() or 0
    if od_count > 0:
        alerts.append(
            CampusOperationalAlertOut(
                id="alert-lib-overdue",
                domain="library",
                level="warning",
                title="Library Circulation Overdue Notices",
                message=f"{od_count} borrowed book(s) have passed their scheduled return due date.",
                timestamp=now,
            )
        )

    # Pending hostel repairs check
    rep_res = await db.execute(
        select(func.count(HostelMaintenanceRequest.id)).where(
            HostelMaintenanceRequest.status == "reported"
        )
    )
    rep_count = rep_res.scalar() or 0
    if rep_count > 0:
        alerts.append(
            CampusOperationalAlertOut(
                id="alert-hostel-maintenance",
                domain="accommodation",
                level="warning",
                title="Hostel Facility Repair Backlog",
                message=f"{rep_count} student maintenance ticket(s) await facilities engineering dispatch.",
                timestamp=now,
            )
        )

    # Pending facility bookings check
    pend_res = await db.execute(
        select(func.count(FacilityReservation.id)).where(FacilityReservation.status == "pending")
    )
    pend_count = pend_res.scalar() or 0
    if pend_count > 0:
        alerts.append(
            CampusOperationalAlertOut(
                id="alert-facility-pending",
                domain="facilities",
                level="info",
                title="Pending Campus Space Reservations",
                message=f"{pend_count} venue reservation request(s) require administrative approval.",
                timestamp=now,
            )
        )

    # Green University Status
    alerts.append(
        CampusOperationalAlertOut(
            id="alert-system-nominal",
            domain="system",
            level="info",
            title="NSBM Campus Infrastructure Nominal",
            message="Smart campus systems, energy grids, and digital learning portals are operating normally.",
            timestamp=now,
        )
    )

    return alerts
