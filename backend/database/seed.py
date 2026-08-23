from datetime import date, datetime, timedelta

from backend.database.session import SessionLocal
from backend.models.appointment import Appointment, AppointmentStatus
from backend.models.finance import Expense, Payment, PaymentStatus
from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.models.settings import ClinicSettings
from backend.models.user import User, UserRole
from backend.utils.security import hash_password


def seed_database():
    with SessionLocal() as session:
        if session.query(User).first():
            return

        admin = User(
            name="Administrador",
            username="admin",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN.value,
            active=True,
        )
        psychologist_user = User(
            name="Marilia Gabriela Gaspar",
            username="marilia",
            password_hash=hash_password("marilia123"),
            role=UserRole.PSYCHOLOGIST.value,
            active=True,
        )
        receptionist = User(
            name="Recepcao",
            username="recepcao",
            password_hash=hash_password("recepcao123"),
            role=UserRole.RECEPTION.value,
            active=True,
        )
        psychologist = Psychologist(
            full_name="Marilia Gabriela Gaspar",
            crp="11/20433",
            phone="(11) 98888-7777",
            email="contato@mariliagasparpsi.local",
            specialty="Desenvolvimento Infantil",
            active=True,
        )
        patient = Patient(
            full_name="Paciente 01",
            cpf="123.456.789-00",
            birth_date=date(1994, 5, 18),
            phone="(11) 97777-6666",
            email="paciente01@email.local",
            address="Endereco de exemplo",
            emergency_contact="Responsavel - (11) 96666-5555",
            notes="Paciente de exemplo para demonstracao.",
            active=True,
        )
        session.add_all([admin, psychologist_user, receptionist, psychologist, patient])
        session.flush()

        appointment = Appointment(
            patient_id=patient.id,
            psychologist_id=psychologist.id,
            scheduled_at=datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1),
            duration_minutes=50,
            status=AppointmentStatus.SCHEDULED.value,
            notes="Primeira sessao de exemplo.",
        )
        payment = Payment(
            patient_id=patient.id,
            due_date=date.today(),
            amount=180.0,
            status=PaymentStatus.PENDING.value,
            payment_method="Pix",
            description="Sessao inicial",
        )
        expense = Expense(
            description="Aluguel da sala",
            amount=1200.0,
            expense_date=date.today(),
            category="Estrutura",
        )
        settings = ClinicSettings(
            clinic_name="Marilia Gabriela Gaspar | Psicologa",
            phone="(11) 3000-0000",
            email="contato@mariliagasparpsi.local",
            address="Atendimento online e presencial",
            default_session_value=180.0,
        )
        session.add_all([appointment, payment, expense, settings])
        session.commit()
