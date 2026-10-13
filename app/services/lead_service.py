
from app.database import add_lead, get_all_leads, delete_lead


class LeadService:
    """Müşteri kayıt işlemlerini yönetir."""

    @staticmethod
    def create(data):
        return add_lead(**data)

    @staticmethod
    def get_all():
        return get_all_leads()

    @staticmethod
    def delete(lead_id):
        return delete_lead(lead_id)
