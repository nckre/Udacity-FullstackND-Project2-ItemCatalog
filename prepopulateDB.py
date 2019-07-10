from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database_setup import Base, AnimalClasses, ClassFamilies, User

# Establish connection to database and create a session


engine = create_engine('sqlite:///animalcatalog.db',
                       connect_args={'check_same_thread': False},
                       poolclass=StaticPool, echo=True)
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


# Create a dummy user
test_user = User(name='Objective Ornithologist',
                 email='ornithologist@test-mail.com',
                 picture='https://upload.wikimedia.org/wikipedia/'
                         'commons/f/f9/Ornithologist_at_field.jpg')

session.add(test_user)
session.commit()

test_class = AnimalClasses(user_id=1, name='Birds',
                           link='https://www.factzoo.com/sites/all/img/birds/'
                                'owls/peeka-boo-boreal.jpg')

session.add(test_class)
session.commit()

test_family = ClassFamilies(user_id=1, name='Owl',
                            description=""" Owls are birds from the order
                             Strigiformes, which includes about 200 species of
                             mostly solitary and nocturnal birds of prey
                             typified by an upright stance.""",
                            distinctive_feature='Sharp talons,binocular vison',
                            male_female='Yes',
                            quantity_on_board=2,
                            animal_class_id=1)

session.add(test_family)
session.commit()

print("Test Data added!")
