class User:
    """
    This class represents a user with attributes ID, name, and age.

    Attributes:
        id (Integer): The ID of the user, serves as the primary key.
        name (String): The name of the user.
        age (Integer): The age of the user.

    Methods:
        greet(): Returns a greeting message that includes the user's name and age.
    """

    id: int
    name: str
    age: int

    def __init__(self, id: int, name: str, age: int) -> None:
        """
        Initialize a User instance.

        Args:
            id (int): The ID of the user.
            name (str): The name of the user.
            age (int): The age of the user.
        """
        self.id = id
        self.name = name
        self.age = age

    def greet(self) -> str:
        """
        Create a greeting message that includes the user's name and age.

        Returns:
            str: A greeting message.
        """
        return f"Hello, my name is {self.name} and I am {self.age} years old."
