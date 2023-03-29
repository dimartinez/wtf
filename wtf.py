import json
import os
import sys
from prompt_toolkit import prompt

FILE_EXTENSION = ".wtf"


def create_or_load_file(filename):
    if not os.path.isfile(filename):
        with open(filename, "w") as f:
            json.dump({"problem": {"name": "", "description": ""}}, f, indent=4)
        print("Se ha creado el archivo vacío", filename)

    with open(filename, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Error: el archivo no está en formato JSON válido.")
            raise

    return data


def save_data_to_file(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def prompt_problem_data():
    name = prompt("Ingrese el nombre del problema: ").strip()
    description = prompt("Ingrese la descripción del problema: ").strip()

    return {"name": name, "description": description}


def prompt_new_name(problem):
    return prompt(f"Ingrese el nuevo nombre del problema ({problem['name']}): ").strip()


def prompt_new_description(problem):
    return prompt(f"Ingrese la nueva descripción del problema ({problem['description']}): ").strip()


def show_problem(problem):
    print("Problema:")
    print(f"  Nombre: {problem['name']}")
    print(f"  Descripción: {problem['description']}\n")


def select_option(filename, data):
    options = {
        "1": lambda: edit_problem(filename, data),
        "2": exit_program
    }

    while True:
        option = prompt(
            "Menú de opciones:\n 1. problema\n 2. salir\nIngrese una opción: ").strip()

        if option in options:
            options[option]()
            break
        else:
            print("Error: opción inválida.")


def edit_problem(filename, data):
    problem = data["problem"]

    if not problem["name"] and not problem["description"]:
        new_problem = prompt_problem_data()
        if new_problem["name"] or new_problem["description"]:
            data["problem"] = new_problem
            save_data_to_file(data, filename)
            show_problem(new_problem)
            return

    show_problem(problem)

    new_name = prompt_new_name(problem)
    new_description = prompt_new_description(problem)

    if not new_name and not new_description:
        return

    problem["name"] = new_name or problem["name"]
    problem["description"] = new_description or problem["description"]
    save_data_to_file(data, filename)
    show_problem(problem)


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
        select_option(filename, data)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nSe ha interrumpido la ejecución del programa.")
