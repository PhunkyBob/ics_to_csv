# -*- coding: utf-8 -*-
"""
Ce script permet de convertir un fichier ICS en un fichier CSV, tout en filtrant les évènements
- selon une date de début et une date de fin
- selon la présence d'un lieu
"""
import re
import csv
from datetime import datetime
import argparse
import os
from gooey import Gooey, GooeyParser
import codecs
import sys

VERSION = "1.0"

def valid_date(s):
    """ Fonction de validation de date : soit vide, soit au format YYYY-MM-DD. """
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "ce n'est pas une date valide: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)

@Gooey(program_name=f"ICS to CSV {VERSION}", default_size=(700, 600), language='french', image_dir='images')
def main():
    # Patch parce que Gooey ne sait pas gérer les entrées / sorties utf-8.
    if sys.stdout.encoding != 'UTF-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'UTF-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

    # Définition des arguments de la ligne de commande par Gooey.
    parser = GooeyParser(
        description="""Script qui transforme un fichier ICS en fichier CSV."""
    )
    parser.add_argument(
        "from_file",
        type=str,
        metavar="Fichier d'entrée",
        help="chemin du fichier ICS à convertir",
        widget='FileChooser',
    )
    parser.add_argument(
        "--output-file",
        "-o",
        default="",
        # nargs='?',
        type=str,
        metavar="Fichier de sortie",
        help="chemin du fichier CSV à créer",
        widget='FileSaver',
    )
    parser.add_argument(
        "--location-only",
        "-l",
        default=False,
        action='store_true',
        metavar="Avec lieu uniquement",
        help="si on ne souhaite que les évènements avec un lieu renseigné",
    )
    parser.add_argument(
        "--from-date",
        "-f",
        default=None,
        type=valid_date,
        metavar="Date de début",
        help="date de début de la période à convertir",
        widget='DateChooser',
    )
    parser.add_argument(
        "--to-date",
        "-t",
        default=None,
        type=valid_date,
        metavar="Date de fin",
        help="date de fin de la période à convertir",
        widget='DateChooser',
    )

    args = parser.parse_args()
    from_file = args.from_file
    to_file = args.output_file
    from_date = args.from_date
    to_date = args.to_date
    location_only = args.location_only

    if not to_file:
        to_file = from_file.replace(".ics", ".csv")

    # Vérification de l'existance du fichier ICS.
    if not os.path.isfile(from_file):
        print(f"ERREUR : Impossible de trouver le fichier \"{from_file}\".")
        exit(1)

    with open(from_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # On récupère les évènements.
    res = re.findall(r"BEGIN:VEVENT(.+?)END:VEVENT", "".join(lines), re.DOTALL)
    to_csv = []
    for elem in res:
        elem = elem.replace("\n ", "")
        current_item = {item.split(':')[0].split(";")[0]: item.split(':')[-1] for item in elem.split("\n") if item}
        if 'DTSTART' in current_item:
            # On transforme la date en datetime.
            if re.match(r"^\d{8}$", current_item['DTSTART']):
                start_date = datetime.strptime(current_item['DTSTART'], "%Y%m%d")
            if re.match(r"^\d{8}T\d{6}Z$", current_item['DTSTART']):
                start_date = datetime.strptime(current_item['DTSTART'], "%Y%m%dT%H%M%SZ")
            # On stocke en plus la date au format "YYYY-MM-DD HH:mm:SS".
            current_item['DTSTART_2'] = start_date
            # On vérifier que la date est dans la période souhaitée et qu'il y a un lieu de défini.
            if (not from_date or start_date >= from_date) and (not to_date or start_date <= to_date):
                if not location_only or ('LOCATION' in current_item and current_item['LOCATION'].strip()):
                    to_csv.append(current_item)

    if not to_csv:
        print("Aucun évènement à convertir.")
        exit(0)

    # On récupère toutes les clés.
    keys = to_csv[0].keys()
    for line in to_csv:
        keys |= line.keys()

    # On écrit le fichier CSV.
    with open(to_file, 'w', encoding='utf-8', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(to_csv)
    print(f"Fichier \"{to_file}\" créé avec succès ({len(to_csv)} éléments).")

if __name__ == '__main__':
    main()
        