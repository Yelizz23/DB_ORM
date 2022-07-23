import sqlalchemy as sq
from sqlalchemy import create_engine
import configparser
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from pprint import pprint
import json

config = configparser.ConfigParser()
config.read('settings.ini')
db_name = config['DB']['db_name']
user = config['DB']['user']
password = config['DB']['password']

DSN = f'postgresql://{user}:{password}@localhost:5432/{db_name}'
Base = declarative_base()
engine = create_engine(DSN)
connection = engine.connect()

# OR

# DSN = 'postgresql://postgres:secret_password@localhost:5432/orm'  # DataSourceName = строка подключения к PostgreSQL
# Base = declarative_base()  # создаём базовый класс, который будет наследоваться
# engine = create_engine(DSN)  # позволяет создать движок, абстракция для подключения к БД
# connection = engine.connect()

# OR

# user = input('Enter user name: ')
# password = input('Enter password: ')
# db_name = input('Enter database name: ')
# DSN = 'postgresql://' + user + ':' + password + '@localhost:5432/' + db_name  # DataSourceName = строка подключения к PostgreSQL
# Base = declarative_base()   # создаём базовый класс, который будет наследоваться
# engine = create_engine(DSN) # позволяет создать движок, абстракция для подключения к БД
# connection = engine.connect()


# класс Base регистрирует всех своих наследников и затем с помощью зарегистрированных объектов создает таблицы в БД
class Publisher(Base):
    __tablename__ = 'publisher'    # название таблицы, которая будет создана в PostgreSQL
    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(length=120), unique=True, nullable=False)

    def __str__(self):
        return f'Publisher {self.id}: {self.name}'


class Book(Base):
    __tablename__ = 'book'
    id = sq.Column(sq.Integer, primary_key=True)
    title = sq.Column(sq.String(length=120), nullable=False)
    publisher_id = sq.Column(sq.Integer, sq.ForeignKey('publisher.id'), nullable=False)

    publisher = relationship(Publisher, backref='book')  # backref автоматические создаёт свойства в таблице Publisher,

    def __str__(self):
        return f'Book {self.id}: {self.title}: {self.publisher_id}'


class Shop(Base):
    __tablename__ = 'shop'
    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(length=120), unique=True)

    def __str__(self):
        return f'Shop {self.id}: {self.name}'


class Stock(Base):
    __tablename__ = 'stock'
    id = sq.Column(sq.Integer, primary_key=True)
    book_id = sq.Column(sq.Integer, sq.ForeignKey('book.id'), nullable=False)
    shop_id = sq.Column(sq.Integer, sq.ForeignKey('shop.id'), nullable=False)
    count = sq.Column(sq.Integer, nullable=False)

    book = relationship(Book, backref='stock')
    shop = relationship(Shop, backref='stock')

    def __str__(self):
        return f'Stock {self.id}: {self.book_id}: {self.shop_id}: {self.count}'


class Sale(Base):
    __tablename__ = 'sale'
    id = sq.Column(sq.Integer, primary_key=True)
    price = sq.Column(sq.Float, nullable=False)
    date_sale = sq.Column(sq.Date, nullable=False)
    stock_id = sq.Column(sq.Integer, sq.ForeignKey('stock.id'), nullable=False)
    count = sq.Column(sq.Integer, nullable=False)

    stock = relationship(Stock, backref='sale')

    def __str__(self):
        return f'Sale {self.id}: {self.price}: {self.date_sale}: {self.stock_id}: {self.count}'


def create_tables(engine):
    Base.metadata.drop_all(engine)  # данные из предыдущих запусков будут удаляться
    Base.metadata.create_all(engine)  # метод create_all создаст все таблицы в БД


publishers = []
books = []
shops = []
stocks = []
sales = []


with open('test_file.json', 'r') as file:
    data = json.load(file)
    for row in data:
        if row['model'] == 'publisher':
            publishers.append(Publisher(name=row['fields']['name']))
        elif row['model'] == 'book':
            books.append(Book(title=row['fields']['title'], publisher_id=row['fields']['publisher']))
        elif row['model'] == 'shop':
            shops.append(Shop(name=row['fields']['name']))
        elif row['model'] == 'stock':
            stocks.append(Stock(book_id=row['fields']['book'], shop_id=row['fields']['shop'],
                                count=row['fields']['count']))
        elif row['model'] == 'sale':
            sales.append(Sale(price=row['fields']['price'], date_sale=row['fields']['date_sale'],
                              count=row['fields']['count'], stock_id=row['fields']['stock']))


def select_publisher():
    publisher_id = input('Please, enter publisher ID or name: ')
    if publisher_id.isdigit():
        publisher_id = int(publisher_id)
        for i in session.query(Publisher).filter(Publisher.id == publisher_id):
            pprint(f'Publisher ID {publisher_id}: {i.name}')
    else:
        for i in session.query(Publisher).filter(Publisher.name == publisher_id).all():
            pprint(f'Publisher ID {i.id}: {i.name}')


def select_shop():
    publ = input('Please, enter publisher ID or name: ')
    if publ.isdigit():
        res = session.query(Shop).join(Stock).join(Book).join(Publisher).filter(Publisher.id==publ).all()
    else:
        res = session.query(Shop).join(Stock).join(Book).join(Publisher).filter(Publisher.name.ilike(f'%{publ}%')).all()
    for i in res:
        print(i.name)


# OR

#def select_shop():
    #result = connection.execute(
        #'SELECT name '
        #'FROM (select shop_id '
        #'FROM (select book.id '
        #'FROM book '
        #'where publisher_id = 1) q1 '
        #'left join stock s on q1.id = s.book_id) q2 '
        #'left join shop sh on q2.shop_id = sh.id '
        #'GROUP BY name;'
    #).fetchall()
    #pprint(result)


create_tables(engine)
Session = sessionmaker(engine)
session = Session()

session.add_all(publishers)
session.add_all(books)
session.add_all(shops)
session.add_all(stocks)
session.add_all(sales)
session.commit()
select_publisher()
select_shop()
