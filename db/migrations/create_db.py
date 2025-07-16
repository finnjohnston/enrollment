from db.database import engine
from db.models import Base

def create_tables():
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    print('Creating all tables...')
    create_tables()
    print('Done.') 