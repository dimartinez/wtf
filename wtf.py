from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt
import networkx as nx
import json
import os
import sys
from prompt_toolkit import prompt
from anytree import Node, RenderTree, ContRoundStyle, PreOrderIter
from queue import Queue
from colorama import init, Fore, Back, Style
import textwrap
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')


# Inicializar colorama
init()

FILE_EXTENSION = ".wtf"
LINE_WRAP_WIDTH = 15


def print_gangster_cat():
    gangster_cat_and_tree = r"""
  /\_/\         A
 / o o \       / \
(   "   )     B---C
  > ^ <      /     \
            D       E

Editor de árboles de problemas.
"""
    for line in gangster_cat_and_tree.split('\n'):
        print(Fore.GREEN + line + Style.RESET_ALL)


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


def look_up_problem_or_cause_by_id(id, data, search_from_cause=False):
    # Verificar que data sea un diccionario
    if not isinstance(data, dict):
        return None

    # Lista de elementos a explorar
    elementos_por_explorar = []

    # Verificar si "problem" está presente en la estructura de datos y si se debe buscar a partir del problema
    if not search_from_cause and "problem" in data:
        elementos_por_explorar.append(data["problem"])
    # Si se debe buscar a partir de una causa, agregar las causas de la causa dada
    elif search_from_cause and "causes" in data:
        elementos_por_explorar.extend(data["causes"])
    else:
        print(f"{Back.RED}{Style.BRIGHT}Error: No hay un problema o causa cargada en la estructura de datos.{Style.RESET_ALL}")
        return None

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

    separator = ": " if problem["description"] else ""
    root = Node(
        f"{Back.RED}{Style.BRIGHT}({problem['id']}){Style.RESET_ALL} {problem['name']}{separator}{problem['description']}", id=problem['id'])

    queue = Queue()
    if "causes" in problem:
        for cause in problem["causes"]:
            queue.put((cause, root))

    while not queue.empty():
        cause, parent = queue.get()

        node = None
        separator = ": " if cause["description"] else ""

        if cause["causes"]:
            node = Node(
                f"{Style.NORMAL}{Back.YELLOW}{Fore.BLACK}({cause['id']}){Style.RESET_ALL} {cause['name']}{separator}{cause['description']}", id=cause['id'], parent=parent)
        else:
            node = Node(
                f"{Back.GREEN}{Fore.BLACK}{Style.BRIGHT}({cause['id']}){Style.RESET_ALL} {cause['name']}{separator}{cause['description']}", id=cause['id'], parent=parent)

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
        show_problem(data["problem"])

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
        "2": lambda: select_cause_option(filename, data) if "problem" in data else print("Error: No hay un problema cargado en el archivo."),
        "3": lambda: draw_tree(data) if "problem" in data else print("Error: No hay un problema cargado en el archivo."),
        "4": lambda: exit_program()
    }

    while True:
        show_problem(data["problem"])

        if "problem" in data:
            option = prompt(
                "Menú de opciones:\n 1. Editar problema\n 2. Submenú de causas\n 3. Dibujar árbol de problema\n 4. Salir del programa\n Ingrese una opción: ").strip()
        else:
            option = prompt(
                "Menú de opciones:\n 1. Cargar problema\n 2. Salir\n Ingrese una opción: ").strip()

        if option in options:
            options[option]()
            if option != "2":  # No romper el bucle si se selecciona el submenú de causa
                break
        else:
            print("Error: opción inválida.")


def draw_tree(data):
    # Crear un grafo dirigido usando la librería networkx
    G = nx.DiGraph()

    def add_causes_to_graph(parent_id, causes):
        # Agregar los nodos y aristas correspondientes para cada causa
        for cause in causes:
            cause_id = cause["id"]
            cause_name = "\n".join(textwrap.wrap(
                cause["name"], width=LINE_WRAP_WIDTH))
            G.add_node(cause_id, name=cause_name)
            G.add_edge(parent_id, cause_id)
            # Si la causa tiene causas anidadas, llamar a la función recursivamente
            if "causes" in cause:
                add_causes_to_graph(cause_id, cause["causes"])

    # Agregar los nodos y aristas correspondientes para el problema principal
    problem = data["problem"]
    problem_id = problem["id"]
    problem_name = "\n".join(textwrap.wrap(
        problem["name"], width=LINE_WRAP_WIDTH))
    G.add_node(problem_id, name=problem_name)
    add_causes_to_graph(problem_id, problem["causes"])

    # Especificar el layout del grafo
    pos = graphviz_layout(G, prog='twopi')

    # Asignar colores a los nodos del grafo
    node_colors = ["#e0e0e0"] * len(G.nodes())
    node_colors[list(G.nodes()).index(problem_id)] = "red"

    def colorize_causes(node_id):
        nonlocal node_colors
        if node_id == problem_id:
            return
        node_colors[list(G.nodes()).index(node_id)] = "yellow"
        if G.out_degree(node_id) == 0:
            node_colors[list(G.nodes()).index(node_id)] = "green"
        for successor in G.successors(node_id):
            colorize_causes(successor)

    for cause in problem["causes"]:
        colorize_causes(cause["id"])

    # Mostrar el gráfico usando matplotlib
    fig, ax = plt.subplots(figsize=(25, 25))
    plt.axis("off")
    plt.title("ÁRBOL DE PROBLEMAS")
    nx.draw(G, pos=pos, with_labels=True, node_color=node_colors,
            edge_color="black", labels=nx.get_node_attributes(G, 'name'),
            node_shape="o", node_size=3000, font_weight="normal", ax=ax)
    plt.savefig("arbol_de_problemas.png", dpi=100, bbox_inches="tight")
    plt.show()


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
        print(
            f"{Back.RED}{Style.BRIGHT}Error: no se puede eliminar el problema raíz.{Style.RESET_ALL}")
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
        print(f"{Back.RED}{Style.BRIGHT}Error: no se puede agregar una causa ya que no hay un problema cargado en el archivo.{Style.RESET_ALL}")
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

    new_parent_id_str = prompt(
        f"Ingrese el nuevo id del padre (actual: {cause['parent_id']}): ").strip()

    try:
        new_parent_id = int(
            new_parent_id_str) if new_parent_id_str else cause["parent_id"]
    except ValueError:
        print(
            f"Error: el valor '{new_parent_id_str}' no es un número entero válido.")
        return

    if new_parent_id != cause["parent_id"]:
        if look_up_problem_or_cause_by_id(new_parent_id, data) is None:
            print(
                f"{Back.RED}{Style.BRIGHT}No existe causa o problema con id {new_parent_id}.{Style.RESET_ALL}")
            return

        # Validar que la causa no se conecte a una causa hija para evitar loops
        if look_up_problem_or_cause_by_id(new_parent_id, cause, search_from_cause=True) is not None:
            print(
                f"{Back.RED}{Style.BRIGHT}Error: no se puede conectar una causa a una de sus causas hijas.{Style.RESET_ALL}")
            return

        # Eliminar la causa del padre anterior
        old_parent = look_up_problem_or_cause_by_id(cause["parent_id"], data)
        old_parent["causes"] = [
            c for c in old_parent["causes"] if c["id"] != cause_id]

        # Asignar la causa al nuevo padre
        cause["parent_id"] = new_parent_id
        new_parent = look_up_problem_or_cause_by_id(new_parent_id, data)
        new_parent["causes"].append(cause)

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

    print_gangster_cat()

    while True:
        select_option(filename, data)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nSe ha interrumpido la ejecución del programa.")
