class BaseRepository:
    def __init__(self, session, model):
        self.session = session
        self.model = model

    def list_all(self):
        return self.session.query(self.model).all()

    def get(self, record_id):
        return self.session.get(self.model, record_id)

    def add(self, entity):
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity):
        self.session.delete(entity)
        self.session.commit()
