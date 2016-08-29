#!/usr/bin/env python

import csv
import subprocess
import glob
import sqlite3

p = subprocess.Popen(["mysql", "-hknownbs.dyndns.org", "-P3307", "-uKNviewer", "-pdbdev249", "-DKnowNet", "-eSELECT s.status_desc, s.table_hash FROM status s WHERE status = 'unmapped';"], stdout=subprocess.PIPE, universal_newlines=True)
#p = subprocess.Popen(["cat", "tempdb.txt"], stdout=subprocess.PIPE, universal_newlines=True)

conn = sqlite3.connect(":memory:")
conn.execute("""CREATE TABLE hashes (
        table_hash TEXT,
        node1 TEXT,
        node2 TEXT,
        PRIMARY KEY (table_hash)
        )""")
conn.execute("""CREATE TABLE status (
        status_desc TEXT,
        table_hash TEXT,
        PRIMARY KEY (table_hash),
        FOREIGN KEY (table_hash) REFERENCES hashes(table_hash)
        )""")

d = {}
for fn in glob.glob('data_representative/*/*/chunks/*.table.*.txt'):
    csvr = csv.reader(open(fn, 'r'), delimiter='\t')
    conn.executemany("INSERT OR IGNORE INTO hashes (table_hash, node1, node2) VALUES (?, ?, ?)", ((line[-1], line[1], line[5]) for line in csvr))

csvr = csv.reader(p.stdout, delimiter='\t')
next(csvr)
conn.executemany("INSERT INTO status (status_desc, table_hash) VALUES (?, ?)", (csvr))

for line in conn.execute("SELECT s.table_hash, h.node1, h.node2, s.status_desc FROM status s, hashes h WHERE s.table_hash = h.table_hash"):
    print('{} {},{} {}'.format(*line))
