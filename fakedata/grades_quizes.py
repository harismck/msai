from random import gauss
from numpy.random import choice
import json
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import os

conn = create_engine(os.getenv("DBURL"))

def main():
    """ Populates two tables with random grades and quiz response data. """

    # Open parameters
    with open('params.json', 'r') as file:
        params = json.loads(file.read())

    # Import necessary data
    students = conn.execute("SELECT id FROM students;").fetchall()
    assessments = conn.execute("SELECT id FROM grades;").fetchall()
    quizes = conn.execute("SELECT id FROM quizes;").fetchall()

    for student in students:

        # Select student level
        level = choice(params['performance_groups'])
        time_level = choice(params['answer_time_groups'])

        # Insert grades
        grades = list(map(lambda x:
                          {
                              "id": x[0],
                              "grade": round5(gauss(level['grades']['mean'], level['grades']['stdev']))
                          }, assessments))
        for grade in grades:
            conn.execute(text(
              """
            INSERT INTO students_grades (student_id, grade_id, grade)
            VALUES (:student_id, :grade_id, :grade)
            """), student_id=student[0], grade_id=grade['id'], grade=grade['grade'])

        # Insert quiz answers
        for quiz in quizes:
            correct = round(gauss(level['answers']['mean'], level['answers']['stdev']), 1)
            if correct > 1:
                correct = 1
            time = round(gauss(time_level['mean'], time_level['stdev']), 2)

            conn.execute(text(
                """
                UPDATE students_quizes
                SET completed = TRUE, time = :time, proportion_correct = :correct
                WHERE student_id = :student_id AND quiz_id = :quiz_id
                RETURNING id;
                """
            ), student_id=student[0], quiz_id=quiz[0], time=time, correct=correct)

def round5(num):
    """ Rounds to the nearest 0.5. """

    return round(num * 2) / 2

if __name__ == '__main__':
    main()
