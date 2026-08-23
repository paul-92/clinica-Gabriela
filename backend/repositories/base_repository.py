class BaseRepository:
    def __init__(self, db, model):
        self.db = db
        self.model = model

    def list_all(self):
        return self.db.query(self.model).all()

    def get(self, record_id):
        return self.db.get(self.model, record_id)

    def create(self, data):
        entity = self.model(**data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity, data):
        for field, value in data.items():
            setattr(entity, field, value)
        self.db.commit()
        self.db.refresh(entity)
        return entity
