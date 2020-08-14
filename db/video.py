from db.session import Session, engine, Base


class Video(Base):

    __tablename__ = 'video'

    def find(cls, id: int):
        """ find record by id """
        session = Session()
        record = session.query(cls).filter(cls.id == id).first()
        session.close()
        return record


Base.prepare(engine, reflect=True)
