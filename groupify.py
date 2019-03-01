import requests
import json
import pyodbc
import os
import argparse
from openpyxl import Workbook

def main():

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', nargs='*', help='Subject.', required=True)
    parser.add_argument('--groupsize', nargs='*', help='Group size.', required=True)
    args = parser.parse_args()

    # Connect to the database
    conn = pyodbc.connect(os.getenv('DBURL'))
    cursor = conn.cursor()

    # Get api url and key from the environment
    api_url = os.getenv('APIURL')
    api_key = os.getenv('APIKEY')

    # Get subject ID
    try:
        id = cursor.execute('SELECT id FROM subjects WHERE name = ?', ' '.join(args.subject)).fetchone()[0]
    except (IndexError, TypeError):
        print("No such subject.")
        exit(1)

    # Form subject extraction query
    subject_query = """
    SELECT student_id, grade, quiz FROM t1 WHERE subject_id = {}
    """.format(id)

    # Perform POST request
    body = {
        "GlobalParameters": {
            'SQL Query Script': subject_query,
            'Number of Centroids': args.groupsize[0]
        }
    }
    body = str.encode(json.dumps(body))
    headers = {
        "Content-Type": "application/json",
        "Authorization": 'Bearer ' + api_key
    }
    resp = requests.post(api_url, data=body, headers=headers)
    if resp.status_code != 200:
        print('Can\'t groupify right now.')
        exit(1)
    results = json.loads(resp.content.decode())['Results']['output1']['value']['Values']

    # Append student names to a spreadsheet
    wb = Workbook()
    sheet = wb.active
    for group in results:
        cursor.execute("SELECT name FROM students WHERE id IN ({});".format(",".join("?" * len(group))), group)
        sheet.append([x[0] for x in cursor.fetchall()])
    wbname = "groups_{subject}.xlsx".format(subject = ''.join(args.subject))
    print("Groups exported to {}.".format(wbname))
    wb.save(wbname)


if __name__ == '__main__':
    main()
