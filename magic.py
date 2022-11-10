#!/usr/bin/env python3
import csv
import sys
import re
import os
import glob

filename = sys.argv[1]
previous_years_dir = sys.argv[2]
capacity_file = "capacities.csv"
output_file = "toewijzingen.csv"

ASSIGNED_CHOICE = "toegewezen"

CAPACITY_CHOICE = "keuze"
CAPACITY_VALUE = "aantal"

TEAM = "Desiree Capel, Nicoline Fokkema, Yvonne de Jong en Sheean Spoel"
MAIL_COLUMN = "mail"

ENROLLMENT_FIRSTNAME = "voornaam"
ENROLLMENT_LASTNAME = "achternaam"
ENROLLMENT_MAIL = "e_mailadres"
ENROLLMENT_DEPT = "afdeling"
ENROLLMENT_CHOICES = ["eerste_keuze", "tweede_keuze", "derde_keuze"]

RANDOM_CHOICE = "» Verras me"
NONE_CHOICE = ["Maak je keuze", "", "---"]
NO_ASSIGNMENT = "**GEEN**"

#
# Start assigning!
#

enrollments = []
capacities = {}
counter = {}

assignments = []


def format_name(enrollment, include_lastname=False):
    first_name = str.join(' ',
                          (part.capitalize() for part in enrollment[ENROLLMENT_FIRSTNAME].strip().split(' ')))
    if include_lastname:
        parts = []
        for part in enrollment[ENROLLMENT_LASTNAME].strip().split(' '):
            if part.lower() in ['van', 'von', 'de', 'der', 'den', 'die']:
                parts.append(part.lower())
            else:
                parts.append(part.capitalize())
        return first_name + ' ' + str.join(' ', parts)

    return first_name


def mail_template(assigned, enrollment):
    name = format_name(enrollment)
    first_choice = enrollment[ENROLLMENT_CHOICES[0]].strip()
    second_choice = enrollment[ENROLLMENT_CHOICES[1]].strip()
    third_choice = enrollment[ENROLLMENT_CHOICES[2]].strip()
    if assigned == first_choice or first_choice == RANDOM_CHOICE:
        # first choice
        content = f"""Je bent geplaatst voor de Wisselwerking {assigned}. We hebben je gegevens doorgegeven aan de contactpersoon van deze Wisselwerking. Deze zal contact met opnemen om verdere afspraken te maken over je deelname.

Heel veel plezier bij je wisselwerking!"""
    elif assigned == second_choice or assigned == third_choice or \
            RANDOM_CHOICE in [second_choice, third_choice]:
        # second, third choice
        if assigned == third_choice:
            ordinal = "derde"
        elif assigned == second_choice:
            ordinal = "tweede"
        else:
            # random!
            ordinal = "vrije"

        content = f"""Helaas was bij jouw eerste keuze voor de Wisselwerking bij {first_choice} geen plek meer. Je bent nu geplaatst bij je {ordinal} keuze: {assigned}.

We hebben je gegevens doorgegeven aan de contactpersoon van deze Wisselwerking. Deze zal contact met opnemen om verdere afspraken te maken over je deelname.

Heel veel plezier bij je wisselwerking!"""
    else:
        # nothing
        content = f"Je hebt je aangemeld voor de Wisselwerking {first_choice}. Helaas waren deze en eventuele verdere keuzes vol."

    return f"""
Beste {name},

{content}

Hartelijke groet,

Team Wisselwerking Geesteswetenschappen
{TEAM}
""".strip()


def get_capacity(choice) -> int:
    if choice == RANDOM_CHOICE:
        return 999
    try:
        capacity = capacities[choice]
        if capacity is None:
            raise KeyError
        return capacity
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


# rename old courses to new names (if known)
renames = {}
with open("renames.csv", mode="r", encoding="utf-8-sig") as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=';')

    for row in csv_reader:
        old = row['old'].lower()
        new = row['new']
        renames[old] = new
        renames[new.lower()] = new


def read_history(base_path: str):
    all_history = {}

    for dir in os.listdir(base_path):
        if dir.lower().startswith('wisselwerking'):
            year_history = read_history_year(
                dir, os.path.join(base_path, dir, "toewijzingen.csv"))

            for email, [dept, assigned] in year_history.items():
                try:
                    all_history[email][0].add(dept)
                    all_history[email][1] += assigned
                except KeyError:
                    all_history[email] = [{dept}, assigned]

    return all_history

def rename_dept(department):
    try:
        return renames[department.lower()]
    except KeyError:
        return department

def read_history_year(dir: str, filepath: str):
    if not os.path.isfile(filepath):
        print(f"{dir} overgeslagen")
        return {}

    history = {}
    with open(filepath, mode="r", encoding="utf-8-sig") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')

        for row in csv_reader:
            email = row[ENROLLMENT_MAIL].lower()
            dept = rename_dept(row[ENROLLMENT_DEPT])

            if email not in history:
                history[email] = [dept, []]

            assigned = rename_dept(row['toegewezen'])

            history[email][1].append(assigned)

    return history


if os.path.exists(capacity_file):
    with open(capacity_file, mode="r", encoding="utf-8-sig") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')

        for row in csv_reader:
            try:
                capacity = int(row[CAPACITY_VALUE])
            except ValueError:
                capacity = None
            except TypeError:
                capacity = None
            capacities[row[CAPACITY_CHOICE]] = capacity

with open(filename, mode="r", encoding='iso8859-15') as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=';')
    form_fieldnames = csv_reader.fieldnames
    line_count = 0

    for row in csv_reader:
        # The top row is the last entry
        enrollments.insert(0, row)
        line_count += 1

history = read_history(previous_years_dir)

# Make sure all possible choices are known
for enrollment in enrollments:
    for choice in map(lambda key: enrollment[key], ENROLLMENT_CHOICES):
        choice = choice.strip()
        if choice in NONE_CHOICE:
            continue
        else:
            counter[choice] = 0


def assign_choice(enrollment, choice):
    try:
        counter[choice] += 1
    except KeyError:
        counter[choice] = 1
    assignments.append((enrollment, choice))
    unassigned.remove(enrollment)

    if choice in choices and counter[choice] >= get_capacity(choice):
        choices.remove(choice)


def show_historic_counts():
    print("""
    TOEWIJZINGEN VAN VORIGE WISSELWERKINGEN:
    """)
    historic_counts = {}
    for items in history.values():
        for item in items[1]:
            try:
                historic_counts[item] += 1
            except KeyError:
                historic_counts[item] = 1

    for item in sorted(historic_counts):
        print(f"{str(historic_counts[item]).rjust(3)} {item}")


def show_counts(show_unassigned=True):
    print("""
    AANTAL AANMELDINGEN:
    """)

    choices = sorted(set(capacities.keys()).union(counter.keys()))
    maxlength = sorted(len(choice) for choice in choices)[-1]
    sum = 0
    empty = []

    for choice in choices:
        count = counter.get(choice, 0)
        if count == 0:
            if choice != RANDOM_CHOICE:
                empty.append(choice)
        else:
            print(f"{str(count).rjust(3)} {choice}")
            sum += count

    print("=" * (maxlength + 4))
    print(f"{str(sum).rjust(3)} TOTAAL")

    if empty:
        print("""
    WISSELWERKINGEN ZONDER TOEWIJZINGEN:
    """)
        for choice in empty:
            print(choice)

    if show_unassigned and unassigned:
        print(f"""
    {len(unassigned)} WISSELWERKERS ZONDER TOEWIJZINGEN:
    """)
        for enrollment in unassigned:
            print(enrollment[ENROLLMENT_MAIL])


choices = list(sorted(set(capacities.keys()).union(counter.keys())))
for item, capacity in capacities.items():
    # possible to close a department
    if capacity == 0:
        choices.remove(item)
unassigned = list(enrollments)

priority = []
# Walk through the choices in iterations
# Give priority on order of choice and within that on order of enrollment
for key in ENROLLMENT_CHOICES:
    for enrollment in enrollments:
        choice = enrollment[key].strip()
        if choice not in NONE_CHOICE:
            priority.append((enrollment, choice))

try:
    while unassigned and choices:
        done = True
        for choice in list(choices):
            for enrollment, enrollment_choice in priority:
                if enrollment in unassigned and enrollment_choice == choice:
                    assign_choice(enrollment, choice)
                    done = False
                    break
        if done:
            break
except KeyboardInterrupt:
    # still store the updated capacities
    save_capacities()
    raise

# assign the random members
choices.remove(RANDOM_CHOICE)


def reassign_random(assignments, history):
    first = True
    for enrollment in list(enrollment for (enrollment, choice) in assignments if choice == RANDOM_CHOICE):
        unassigned.append(enrollment)
        email = enrollment[ENROLLMENT_MAIL]
        if first:
            print("\n\n===TUSSENSTAND===\n\n")
            show_historic_counts()
            show_counts(False)
            first = False
        depts = history[email][0]
        print(f"\n\n{email} ({'; '.join(depts)}) moet verrast worden")
        if email in history:
            print("Deed eerder de volgende wisselwerkingen: " +
                  ", ".join(history[email][1]))
        else:
            print("Wisselwerking-newbie!")

        while True:
            choice = input("Wijs een andere wisselwerking toe: ")
            if (0 if choice not in counter else counter[choice]) < get_capacity(choice):
                for item in assignments:
                    check_enrolment, _ = item
                    if check_enrolment == enrollment:
                        assignments.remove(item)
                        break
                assign_choice(enrollment, choice)
                counter[RANDOM_CHOICE] -= 1
                break
            else:
                print("Zit al vol!")


reassign_random(assignments, history)

save_capacities()

show_counts()

# Store the assignments
with open(output_file, mode="w", encoding="utf-8-sig") as csv_file:
    fieldnames = [ASSIGNED_CHOICE, ENROLLMENT_MAIL, MAIL_COLUMN] + [field for field in form_fieldnames if field != MAIL_COLUMN]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=';')

    writer.writeheader()
    for (row, assigned) in assignments:
        writer.writerow({
            ASSIGNED_CHOICE: assigned,
            "mail": mail_template(assigned, row),
            **row
        })

# Store the assignments per choice - to mail the organizers
output_prepath = str.join('.', output_file.split('.')[:-1])


def output_text_file(choice, escape=True):
    return output_prepath + '.' + (choice if not escape else re.sub(r'[\*\(\) \-\.\&]+', '-', choice)) + '.txt'


existing_files = glob.glob(output_text_file('*', False))

for choice in sorted(counter):
    if choice == RANDOM_CHOICE:
        continue
    count = counter[choice]
    target = output_text_file(choice)
    try:
        existing_files.remove(target)
    except ValueError:
        pass
    with open(target, mode="w", encoding="utf-8-sig") as txt_file:
        choice_assignments = []
        for (row, assigned) in assignments:
            if assigned == choice:
                choice_assignments.append(
                    f"{format_name(row, True)} <{row[ENROLLMENT_MAIL]}> ({rename_dept(row[ENROLLMENT_DEPT].strip())})\n")


        if count > 0:
            txt_file.writelines([f"""Beste organisator,

Leuk dat je je hebt opgegeven om een wisselwerking te organiseren! Voor de wisselwerking {choice} hebben de volgende {count} person(en) zich aangemeld:

"""] +
                            choice_assignments +
                            [f"""
Zou je zo snel mogelijk contact willen opnemen met deze mensen om afspraken te maken over de wisselwerking? 

Heel veel plezier bij de wisselwerking!

Hartelijke groet,

Team Wisselwerking Geesteswetenschappen
{TEAM}
"""])
        else:
            txt_file.writelines([f"""Beste organisator,

Helaas heeft dit jaar niemand zich aangemeld voor de Wisselwerking {choice}.

Dank dat je een Wisselwerking wilde organiseren. We hopen dat je volgend jaar weer meedoet!

Hartelijke groet,

Team Wisselwerking Geesteswetenschappen
{TEAM}
"""])

# Clear existing files, which are no longer assigned
for existing_file in existing_files:
    os.remove(existing_file)

print("DONE! Plaats toewijzingen.csv op de O-schijf")
