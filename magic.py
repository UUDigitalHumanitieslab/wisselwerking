#!/usr/bin/env python3
import csv
import sys
import os

filename = sys.argv[1]
capacity_file = "capacities.csv"
output_file = "toewijzingen.csv"

ASSIGNED_CHOICE = "toegewezen"

CAPACITY_CHOICE = "keuze"
CAPACITY_VALUE = "aantal"

TEAM = "Desiree Capel, Nicoline Fokkema, Yvonne de Jong en Sheean Spoel"
MAIL_COLUMN = "mail"

ENROLLMENT_NAME = "naam"
ENROLLMENT_PHONE = "telefoonnummer"
ENROLLMENT_CHOICES = ["eerste_keuze", "tweede_keus", "derde_keus"]

NONE_CHOICE = "Maak je keuze"

#
# Start assigning!
#

enrollments = []
capacities = {}
counter = {}

assignments = []

def format_name(enrollment):
    name = enrollment[ENROLLMENT_NAME]
    return name.strip().split(' ')[0].capitalize()

def mail_template(assigned, enrollment):
    name = format_name(enrollment)
    first_choice = enrollment[ENROLLMENT_CHOICES[0]].strip()
    second_choice = enrollment[ENROLLMENT_CHOICES[1]].strip()
    if assigned == first_choice:
        # first choice
        explain_choice = f"de Wisselwerking {assigned}. Het doet ons plezier je te laten weten dat je geplaatst bent voor deze Wisselwerking"
    elif assigned == NONE_CHOICE:
        # nothing
        explain_choice = f"de Wisselwerking {assigned}. Helaas waren deze en eventuele verdere keuzes vol"
    else:
        # second, third choice
        ordinal = "tweede" if assigned == second_choice else "derde"
        explain_choice = f"de Wisselwerking. Helaas was bij jouw eerste keuze {first_choice} geen plek meer. Je bent nu geplaatst bij je {ordinal} keuze: {assigned}"
    
    return f"""
Beste {name},

Je hebt je aangemeld voor {explain_choice}.

We hebben je gegevens doorgegeven aan de contactpersoon van jouw Wisselwerking. Hij of zij neemt contact met je op om verdere afspraken te maken over je deelname.

Hartelijke groet,

Team Wisselwerking Geesteswetenschappen
{TEAM}
""".strip()

if os.path.exists(capacity_file):
    with open(capacity_file, mode="r", encoding="utf-8-sig") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')

        for row in csv_reader:
            capacities[row[CAPACITY_CHOICE]] = int(row[CAPACITY_VALUE])

with open(filename, mode="r", encoding='iso8859-15') as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=';')
    form_fieldnames = csv_reader.fieldnames
    line_count = 0

    for row in csv_reader:
        # The top row is the last entry
        enrollments.insert(0, row)
        line_count += 1


def get_capacity(choice):
    try:
        return capacities[choice]
    except KeyError:
        while True:
            value = input(f"Capacity for {choice}? ")
            try:
                parsed = int(value)
                capacities[choice] = parsed
                return parsed
            except ValueError:
                print("NOPE")
                pass


def assign(enrollment):
    for choice in map(lambda key: enrollment[key], ENROLLMENT_CHOICES):
        choice = choice.strip()
        if choice == NONE_CHOICE:
            continue
        if not choice in counter or \
                counter[choice] < get_capacity(choice):
            return choice
    return None


def save_capacities():
    with open(capacity_file, mode="w", encoding="utf-8-sig") as csv_file:
        fieldnames = [CAPACITY_CHOICE, CAPACITY_VALUE]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=';')

        writer.writeheader()
        for (choice, value) in capacities.items():
            writer.writerow({
                CAPACITY_CHOICE: choice,
                CAPACITY_VALUE: value
            })


try:
    # assign everybody to their first choice which isn't filled yet
    # ordered by their enrolment date
    for enrollment in enrollments:
        assigned = assign(enrollment)

        if assigned != None:
            try:
                counter[assigned] += 1
            except KeyError:
                counter[assigned] = 1

        assignments.append((enrollment, assigned or "**GEEN**"))
except KeyboardInterrupt:
    # still store the updated capacities
    save_capacities()
    raise

save_capacities()

print("""
AANTAL AANMELDINGEN:
""")

for choice in sorted(counter):
    print(f"{choice}\t{counter[choice]}")

# Store the assignments
with open(output_file, mode="w", encoding="utf-8-sig") as csv_file:
    fieldnames = [ASSIGNED_CHOICE, MAIL_COLUMN] + form_fieldnames
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=';')

    writer.writeheader()
    for (row, assigned) in assignments:
        writer.writerow({
            ASSIGNED_CHOICE: assigned,
            "mail": mail_template(assigned, row),
            **row
        })
