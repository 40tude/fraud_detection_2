from mon_module.user import User
from pathlib import Path

if __name__ == "__main__":
    bob = User(80386, "Zoubida", 42)
    print(bob.greet())
