import json
import os
import sys
from prompt_toolkit import prompt
from anytree import Node, RenderTree, ContRoundStyle, PreOrderIter
from queue import Queue

FILE_EXTENSION = ".wtf"


def create_or_load_file(filename):

    if not os.path.isfile(filename):
        with open(filename, "w") as f:
            json.dump({
                "metadata": {
                    "last_id": 1
                },
                "problem": {
                    "id": 1,
                    "name": "",
                    "description": "",
                    "causes": []
                }
            }, f, indent=4)
            print(f"Se ha creado el archivo vacío {filename}.")

    with open(filename) as f:
        data = json.load(f)

    # Si el "last_id" es menor que el "id" del "problem", actualizar "last_id" al "id" del "problem"
    if data["metadata"]["last_id"] < data["problem"]["id"]:
        data["metadata"]["last_id"] = data["problem"]["id"]

    return data


def look_up_problem_or_cause_by_id(id, data):
    # Verificar que data sea un diccionario
    if not isinstance(data, dict):
        return None

    # Lista de elementos a explorar
    elementos_por_explorar = [data["problem"]]

    # Ciclo de exploración
    while elementos_por_explorar:
        # Tomar el último elemento de la lista
        elemento_actual = elementos_por_explorar.pop()

        # Verificar si el elemento actual es un diccionario y si su 'id' es igual al buscado
        if isinstance(elemento_actual, dict) and elemento_actual.get("id") == id:
            # Si se encuentra, se devuelve el elemento actual
            return elemento_actual

        # Verificar si el elemento actual es un diccionario y si tiene una lista de "causes"
        if isinstance(elemento_actual, dict) and "causes" in elemento_actual:
            # Agregar cada elemento de la lista a la lista de elementos a explorar
            elementos_por_explorar.extend(elemento_actual["causes"])

    # Si no se encuentra el elemento, se devuelve None
    return None


def save_data_to_file(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f)
        print(f"El archivo {filename} ha sido guardado exitosamente.")


def prompt_problem_data():
    name = prompt("Ingrese el nombre del problema: ").strip()
    description = prompt("Ingrese la descripción del problema: ").strip()

    return {"name": name, "description": description}


def prompt_new_name(problem):
    return prompt(f"Ingrese el nuevo nombre del problema ({problem['name']}): ").strip()


def prompt_new_description(problem):
    return prompt(f"Ingrese la nueva descripción del problema ({problem['description']}): ").strip()


def show_problem(problem):
    print("\n")

    root = Node(
        f"({problem['id']}) {problem['name']}: {problem['description']}", id=problem['id'])

    queue = Queue()
    if "causes" in problem:
        for cause in problem["causes"]:
            queue.put((cause, root))

    while not queue.empty():
        cause, parent = queue.get()
        node = Node(
            f"({cause['id']}) {cause['name']}: {cause['description']}", id=cause['id'], parent=parent)

        if "causes" in cause:
            for sub_cause in cause["causes"]:
                queue.put((sub_cause, node))

    for pre, _, node in RenderTree(root, style=ContRoundStyle()):
        print("%s%s" % (pre, node.name))

    print("\n")


def select_cause_option(filename, data):
    options = {
        "1": lambda: new_cause(filename, data),
        "2": lambda: delete_cause(filename, data),
        "3": lambda: edit_cause(filename, data),
        "4": lambda: None  # Regresar al menú principal
    }

    while True:
        option = prompt(
            "Submenú de causa:\n 1. Nueva causa\n 2. Eliminar causa\n 3. Editar causa\n 4. Regresar al menú principal\n Ingrese una opción: ").strip()

        if option in options:
            options[option]()
            if option == "4":
                break
        else:
            print("Error: opción inválida.")


def select_option(filename, data):
    options = {
        "1": lambda: edit_problem(filename, data),
        "2": lambda: exit_program(),
        "3": lambda: select_cause_option(filename, data) if "problem" in data else print("Error: No hay un problema cargado en el archivo.")
    }

    while True:
        if "problem" in data:
            option = prompt(
                "Menú de opciones:\n 1. Editar problema\n 2. Salir\n 3. Operaciones de causa\n Ingrese una opción: ").strip()
        else:
            option = prompt(
                "Menú de opciones:\n 1. Cargar problema\n 2. Salir\n Ingrese una opción: ").strip()

        if option in options:
            options[option]()
            if option != "3":  # No romper el bucle si se selecciona el submenú de causa
                break
        else:
            print("Error: opción inválida.")


def delete_cause(filename, data):
    # Verificar si hay un problema cargado en el archivo
    if "problem" not in data:
        print("Error: no se puede eliminar una causa ya que no hay un problema cargado en el archivo.")
        return

    # Solicitar el ID de la causa a eliminar
    cause_id_str = prompt("Ingrese el id de la causa a eliminar: ").strip()

    # Validar que el ID proporcionado sea un número entero válido
    try:
        cause_id = int(cause_id_str)
    except ValueError:
        print(
            f"Error: el valor '{cause_id_str}' no es un número entero válido.")
        return

    # Verificar si el ID corresponde al problema raíz
    if cause_id == data["problem"]["id"]:
        print("Error: no se puede eliminar el problema raíz.")
        return

    # Buscar la causa a eliminar en la estructura de datos
    cause = look_up_problem_or_cause_by_id(cause_id, data)
    if cause is None:
        print(f"No existe causa con id {cause_id}.")
        return

    # Buscar el nodo padre de la causa a eliminar en la estructura de datos
    parent = look_up_problem_or_cause_by_id(cause["parent_id"], data)
    if parent is None:
        print(f"No existe nodo padre con id {cause['parent_id']}.")
        return

    # Verificar si la causa a eliminar tiene causas hijas
    # y preguntar al usuario si desea conservarlas
    if "causes" in cause and cause["causes"]:
        response = prompt(
            f"La causa '{cause['name']}' tiene {len(cause['causes'])} causas hijas. ¿Desea conservarlas? (s/n): ").strip().lower()

        if response == "s":
            # Si el usuario desea conservar las causas hijas, agregarlas al nodo padre
            for sub_cause in cause["causes"]:
                sub_cause["parent_id"] = parent["id"]
            parent["causes"].extend(cause["causes"])

    # Eliminar la causa de la estructura de datos
    parent["causes"] = [c for c in parent["causes"] if c["id"] != cause_id]

    # Mostrar un mensaje de confirmación
    print(f"La causa '{cause['name']}' ha sido eliminada del problema.")

    # Guardar los cambios en el archivo
    save_data_to_file(data, filename)


def get_last_id(data):
    # Obtener el último identificador utilizado
    last_id = data["metadata"]["last_id"]
    return last_id


def new_cause(filename, data):
    # Validar que la estructura de datos contenga un problema
    if "problem" not in data:
        print("Error: no se puede agregar una causa ya que no hay un problema cargado en el archivo.")
        return

    # Solicitar nombre y descripción de la nueva causa
    cause_name = prompt("Ingrese el nombre de la causa: ").strip()
    cause_description = prompt("Ingrese la descripción de la causa: ").strip()

    # Solicitar el id de la causa padre
    parent_id_str = prompt(
        "Ingrese el id de la causa padre (Enter si es hija directa del problema): ").strip()

    # Validar que el id proporcionado sea un número entero válido
    try:
        parent_id = int(parent_id_str) if parent_id_str else None
    except ValueError:
        print(
            f"Error: el valor '{parent_id_str}' no es un número entero válido.")
        return

    # Buscar el nodo padre en la estructura de datos
    if parent_id is not None:
        parent = look_up_problem_or_cause_by_id(parent_id, data)

        if parent is None:
            print(f"No existe nodo con id {parent_id}.")
            return

    # Obtener el último identificador utilizado y generar un nuevo identificador único
    last_id = get_last_id(data)
    new_id = last_id + 1

    # Crear un nuevo diccionario de causa con el identificador único y los datos proporcionados
    new_cause = {
        "id": new_id,
        "parent_id": parent_id if parent_id is not None else data["problem"]["id"],
        "name": cause_name,
        "description": cause_description,
        "causes": []
    }

    # Agregar la nueva causa a la estructura de datos
    if parent_id is None:
        data["problem"]["causes"].append(new_cause)
    else:
        parent["causes"].append(new_cause)

    # Actualizar el último identificador utilizado en los metadatos
    data["metadata"]["last_id"] = new_id

    # Guardar los cambios en el archivo
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    # Mostrar un mensaje de confirmación
    print(
        f"La causa '{cause_name}' ha sido agregada al problema con identificador {new_id}.")


def edit_cause(filename, data):
    cause_id_str = prompt("Ingrese el id de la causa a editar: ").strip()

    try:
        cause_id = int(cause_id_str)
    except ValueError:
        print(
            f"Error: el valor '{cause_id_str}' no es un número entero válido.")
        return

    cause = look_up_problem_or_cause_by_id(cause_id, data)

    if cause is None:
        print(f"No existe causa con id {cause_id}.")
        return

    new_name = prompt(
        f"Ingrese el nuevo nombre de la causa ({cause['name']}): ").strip()
    new_description = prompt(
        f"Ingrese la nueva descripción de la causa ({cause['description']}): ").strip()

    cause["name"] = new_name.strip() or cause["name"]
    cause["description"] = new_description.strip() or cause["description"]

    save_data_to_file(data, filename)


def edit_problem(filename, data):
    problem = data["problem"]
    problem_id = problem["id"]
    new_name = prompt_new_name(problem)
    new_description = prompt_new_description(problem)

    if not new_name.strip() and not new_description.strip():
        return

    problem["name"] = new_name.strip() or problem["name"]
    problem["description"] = new_description.strip() or problem["description"]

    if not problem["name"] and not problem["description"]:
        return

    if "causes" in problem:
        causes = problem["causes"]
        problem.pop("causes")
        problem["causes"] = causes

    problem["id"] = problem_id

    save_data_to_file(data, filename)


def exit_program():
    sys.exit(0)


def main():
    if len(sys.argv) < 2:
        print("Error: se debe proporcionar un nombre de archivo.")
        return

    filename = sys.argv[1]

    if not filename.endswith(FILE_EXTENSION):
        print(f"Error: el archivo debe tener extensión '{FILE_EXTENSION}'.")
        return

    data = create_or_load_file(filename)

    while True:
        show_problem(data["problem"])
        select_option(filename, data)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nSe ha interrumpido la ejecución del programa.")
