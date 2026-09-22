from datetime import date, datetime, timedelta

from backend.database.session import SessionLocal
from backend.models.appointment import Appointment, AppointmentStatus
from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.models.settings import ClinicSettings
from backend.models.user import User, UserRole
from backend.services.finance_service import FinanceService
from backend.utils.security import hash_password
from app.utils.initial_admin import get_initial_admin_config


def seed_database(session_factory=None):
    sessions = session_factory or SessionLocal
    with sessions() as session:
        if not session.query(User).first():
            initial_admin = get_initial_admin_config()
            if initial_admin:
                session.add(User(
                    name=initial_admin["name"],
                    username=initial_admin["username"],
                    password_hash=hash_password(initial_admin["password"]),
                    role=UserRole.ADMIN.value,
                    active=True,
                ))

        if session.query(Patient).first():
            session.commit()
            return
        seed_actor = User(
            name="Ator Sintetico do Seed",
            username="__seed_finance_actor__",
            password_hash="!disabled-seed-account!",
            role=UserRole.ADMIN.value,
            active=False,
            password_reset_required=True,
        )
        psychologist = Psychologist(
            full_name="Marilia Gabriela Gaspar",
            crp="11/20433",
            crp_region="11",
            crp_number="20433",
            crp_status="apt",
            phone="(11) 98888-7777",
            email="contato@mariliagasparpsi.local",
            specialty="Desenvolvimento Infantil",
            active=True,
        )
        patient = Patient(
            full_name="Paciente 01",
            cpf="52998224725",
            cpf_status="verified",
            birth_date=date(1994, 5, 18),
            phone="(11) 97777-6666",
            email="paciente01@email.local",
            address="Endereco de exemplo",
            emergency_contact="Responsavel - (11) 96666-5555",
            notes="Paciente de exemplo para demonstracao.",
            active=True,
        )
        session.add_all([seed_actor, psychologist, patient])
        session.flush()

        appointment = Appointment(
            patient_id=patient.id,
            psychologist_id=psychologist.id,
            scheduled_at=datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1),
            duration_minutes=50,
            status=AppointmentStatus.SCHEDULED.value,
            notes="Primeira sessao de exemplo.",
        )
        settings = ClinicSettings(
            clinic_name="Marilia Gabriela Gaspar | Psicologa",
            phone="(11) 3000-0000",
            email="contato@mariliagasparpsi.local",
            address="Atendimento online e presencial",
            default_session_value=180.0,
        )
        session.add_all([appointment, settings])
        session.flush()

        finance = FinanceService(session)
        category = finance.create_category({"name": "Estrutura", "active": True}, seed_actor)
        finance.create_payment(
            {
                "patient_id": patient.id,
                "competence_date": date.today(),
                "due_date": date.today(),
                "amount_cents": 18000,
                "payment_method": "Pix",
                "description": "Sessao inicial",
            },
            seed_actor,
        )
        finance.create_expense(
            {
                "description": "Aluguel da sala",
                "amount_cents": 120000,
                "expense_date": date.today(),
                "competence_date": date.today(),
                "category_id": category.id,
            },
            seed_actor,
        )
