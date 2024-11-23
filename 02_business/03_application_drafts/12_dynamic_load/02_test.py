import importlib
import inspect


# -----------------------------------------------------------------------------
module_name = "mon_module.user"
module = importlib.import_module(module_name)


# -----------------------------------------------------------------------------
classes = []
functions = []

for name in dir(module):
    attribute = getattr(module, name)
    if inspect.isclass(attribute):
        classes.append(name)
    elif inspect.isfunction(attribute):
        functions.append(name)

print("Classes disponibles:", classes)
print("Fonctions disponibles:", functions)


# -----------------------------------------------------------------------------
for current_classe in classes:
    ClassToInstantiate = getattr(module, current_classe)
    methodes = [m[0] for m in inspect.getmembers(ClassToInstantiate, predicate=inspect.isfunction)]
    print(f"Méthodes de {current_classe}:", methodes)

    attributs = [
        a for a in dir(ClassToInstantiate) if not callable(getattr(ClassToInstantiate, a)) and not a.startswith("__")
    ]
    print(f"Attributs de l'instance de {current_classe}:", attributs)


# -----------------------------------------------------------------------------
class_name = "User"
if class_name in classes:
    ClassToInstantiate = getattr(module, class_name)
    instance = ClassToInstantiate(80386, "Zoubida", 42)
    print(f"Instance de {class_name} créée:", instance)
    print(instance.greet())


# -----------------------------------------------------------------------------
function_name = "Zoubida"
if function_name in functions:
    function_to_call = getattr(module, function_name)
    result = function_to_call(12, 36)
    print(f"Résultat de l'appel de {function_name}:", result)
