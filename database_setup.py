import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import backref

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class AnimalClasses(Base):
    __tablename__ = 'animal_classes'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    link = Column(String(500), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', foreign_keys=[user_id])
    animal_families = relationship('ClassFamilies', cascade="""all,
                                   delete-orphan""")

    @property
    def serialize(self):
        return {
           'name': self.name,
           'id': self.id,
           'link': self.link,
           'user_id': self.user_id,
           }


class ClassFamilies(Base):
    __tablename__ = 'class_family'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    distinctive_feature = Column(String(250))
    quantity_on_board = Column(Integer)
    male_female = Column(String(3))
    animal_class_id = Column(Integer, ForeignKey('animal_classes.id'))
    animal_classes = relationship('AnimalClasses',
                                  foreign_keys=[animal_class_id])
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', foreign_keys=[user_id])

    @property
    def serialize(self):
        return {
           'name': self.name,
           'description': self.description,
           'id': self.id,
           'distinctive_feature': self.distinctive_feature,
           'quantity_on_board': self.quantity_on_board,
           'male_female': self.male_female,
           'animal_class_id': self.animal_class_id,
           'user_id': self.user_id,
           }


engine = create_engine('sqlite:///animalcatalog.db')


Base.metadata.create_all(engine)
