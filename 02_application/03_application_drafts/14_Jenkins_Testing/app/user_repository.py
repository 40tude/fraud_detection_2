from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .user_mock import User_mock


class UserRepository:
    """
    This class is used to interact with the database and perform operations on
    the User objects.

    Attributes:
        engine (create_engine): An instance of SQLAlchemy Engine for database interaction.
        session (Session): An instance of SQLAlchemy Session for transactional scope.

    Methods:
        get_users() -> list[User]:
            Fetches all User records from the database and returns them.
    """

    def __init__(self, db_url: str) -> None:
        """
        Initializes the UserRepository instance with a database connection.

        Args:
            db_url (str): The database connection URL.
        """
        self.engine = create_engine(db_url)                 # sqlalchemy
        session: Session = sessionmaker(bind=self.engine)   # sqlalchemy.orm
        self.session = session()

    def get_users(self) -> list[User_mock]:
        """
        Fetches all User records from the database.

        Returns:
            list[User]: A list of User instances.
        """
        users = self.session.query(User_mock).all()
        return users