#!/usr/bin/env python3
import csv
import os
import re
from typing import Dict, Tuple, List
from .settings import ASSIGNED_CHOICE, ENROLLMENT_MAIL, ENROLLMENT_DEPT,  HISTORY_YEARS, HISTORY_HOW_MANY


class Enrollment:
    def __init__(self, email: str, years: Tuple[int, int], from_dept: str, assigned_dept: str):
        self.email = email
        self.years = years
        self.from_dept = from_dept
        self.assigned_dept = assigned_dept


class EnrollmentCollection:
    def __init__(self, items: List[Enrollment]):
        self.items = items
        self.ids = {}

    def to_rows(self):
        for enrollment in self.items:
            yield [enrollment.email, f'{enrollment.years[0]}-{enrollment.years[1]}', enrollment.from_dept, enrollment.assigned_dept]

    def list_from_depts(self):
        depts = set()
        for enrollment in self.items:
            depts.add(enrollment.from_dept)
        return depts

    def list_assigned(self):
        depts = set()
        for enrollment in self.items:
            depts.add(enrollment.assigned_dept)
        return depts

    def by_email(self, email):
        for item in self.items:
            if item.email == email:
                yield item

    def __get_id(self, email):
        try:
            return self.ids[email]
        except KeyError:
            new_id = len(self.ids) + 1
            self.ids[email] = new_id
            return new_id

    def to_csv(self):
        self.items.sort(key=lambda enrollment: enrollment.years[0])

        participant_count: Dict[int, int] = {}

        with open('history.csv', 'w', encoding='utf-8-sig') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=[
                                    'id', 'count', HISTORY_HOW_MANY, HISTORY_YEARS, ENROLLMENT_DEPT, ASSIGNED_CHOICE], delimiter=';')

            writer.writeheader()
            for enrollment in self.items:
                participant_id = self.__get_id(enrollment.email)
                try:
                    how_many = participant_count[participant_id] + 1
                except KeyError:
                    participant_count[participant_id] = 0
                    how_many = 1
                participant_count[participant_id] += 1
                writer.writerow({
                    'id': participant_id,
                    'count': 1,  # makes pivot tables easier to create
                    HISTORY_HOW_MANY: how_many,
                    HISTORY_YEARS: f'{enrollment.years[0]}-{enrollment.years[1]}',
                    ENROLLMENT_DEPT: enrollment.from_dept,
                    ASSIGNED_CHOICE: enrollment.assigned_dept
                })

        # new participants each year
        per_year: Dict[str, List[int]] = {}

        for enrollment in self.items:
            years = f'{enrollment.years[0]}-{enrollment.years[1]}'
            participant_id = self.__get_id(enrollment.email)
            try:
                per_year[years].append(participant_id)
            except KeyError:
                per_year[years] = [participant_id]

        with open('history_new_participants.csv', 'w', encoding='utf-8-sig') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=[
                                    HISTORY_YEARS, 'old', 'new', 'completely_new'], delimiter=';')

            writer.writeheader()
            previous_year: List[int] = []
            all_years: List[int] = []
            for years, participants in per_year.items():
                old_count = 0
                count = 0
                new_count = 0
                for p in participants:
                    if p in all_years:
                        old_count += 1
                    else:
                        new_count += 1
                    if p not in previous_year:
                        count += 1

                writer.writerow({
                    HISTORY_YEARS: years,
                    'old': old_count,
                    'new': count,
                    'completely_new': new_count
                })

                previous_year = participants
                all_years += participants

        # how many times do people participate over the years?
        histogram: Dict[int, int] = {}
        for participant_id, participant_count in participant_count.items():
            try:
                histogram[participant_count] += 1
            except KeyError:
                histogram[participant_count] = 1

        with open('history_histogram.csv', 'w', encoding='utf-8-sig') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=[
                                    'times', 'count'], delimiter=';')

            writer.writeheader()
            for times, count in histogram.items():
                writer.writerow({
                    'times': times,
                    'count': count
                })


# rename old courses to new names (if known)
renames: Dict[str, str] = {}
with open("renames.csv", mode="r", encoding="utf-8-sig") as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=';')

    for row in csv_reader:
        old = row['old'].lower().strip()
        new = row['new'].strip()
        renames[old] = new
        renames[new.lower()] = new


def read_history(base_path: str, all_history=None) -> EnrollmentCollection:
    if all_history is None:
        all_history: List[Enrollment] = []

    for dir in os.listdir(base_path):
        if dir.lower().startswith('wisselwerking'):
            year_history = read_history_year(
                dir, os.path.join(base_path, dir, "toewijzingen.csv"))

            for enrollment in year_history:
                all_history.append(enrollment)
        elif dir.lower().startswith('archief'):
            read_history(os.path.join(base_path, dir), all_history)

    return EnrollmentCollection(all_history)


def rename_dept(department: str) -> str:
    department = department.replace('\u2013', '-')
    department = re.sub(r'\s+', ' ', department)
    department = department.strip()
    try:
        return renames[department.lower()]
    except KeyError:
        return department


def read_history_year(dir: str, filepath: str) -> List[Enrollment]:
    if not os.path.isfile(filepath):
        print(f"{dir} overgeslagen")
        return []

    history: List[Enrollment] = []
    years = list(map(lambda x: int(x), re.findall(r'\d{4}', dir)))
    with open(filepath, mode="r", encoding="utf-8-sig") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')

        for row in csv_reader:
            email = row[ENROLLMENT_MAIL].lower()
            dept = rename_dept(row[ENROLLMENT_DEPT])
            assigned = rename_dept(row['toegewezen'])
            history.append(Enrollment(
                email,
                years,
                dept,
                assigned
            ))

    return history
