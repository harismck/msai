from sqlalchemy import create_engine
from sqlalchemy.sql import text
import os
import json
import itertools

conn = create_engine(os.getenv("DBPASS"))


def main():
    """ Populates five database tables with data. All data is taken from the fakedata folder. """

    # Insert students
    with open('students', 'r') as students:
        for student in students.read().splitlines():
            conn.execute(text("INSERT INTO students (name) VALUES (:name);"), name=student)

    # Insert subjects and assessments
    with open('subjects', 'r') as subjects, open('assessments.json', 'r') as assessments:
        assessments = json.loads(assessments.read())
        for subject in subjects.read().splitlines():
            id = conn.execute(text("INSERT INTO subjects (name) VALUES (:name) RETURNING id;"),
                              name=subject).fetchone()[0]
            for assessment in assessments:
                conn.execute(text(
                    """
                    INSERT INTO grades (subject_id, assessment, weight) 
                    VALUES (:subject_id, :assessment, :weight)
                    """
                ), subject_id=id, assessment=assessment['name'], weight=assessment['weight'])

    # Create quizes (10 for each subject)
    subjects = conn.execute("SELECT id FROM subjects;").fetchall()
    quizes = []
    for i in range(len(subjects) * 10):
        quizes.append((i))
        conn.execute(text(
            """
            INSERT INTO quizes (id, subject_id)
            VALUES (:id, :subject_id);
            """), id=i, subject_id=subjects[i % len(subjects)][0]
        )

    # Assign quizes to students
    students = conn.execute("SELECT id FROM students;").fetchall()
    for student, quiz in itertools.product([i[0] for i in students], quizes):
        conn.execute(text(
            """
            INSERT INTO students_quizes (student_id, quiz_id, completed, time)
            VALUES (:student_id, :quiz_id, :completed, :time);
            """), student_id=student, quiz_id=quiz, completed=False, time=None
        )


if __name__ == '__main__':
    main()
