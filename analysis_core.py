"""Deterministic record triage; no species-discovery claims or fabricated features."""
import csv
import io
import math

MISSING = {'', 'unknown', 'nan', 'none', 'null', 'n/a', 'na', 'sp', 'sp.'}

def known(value):
    return str(value or '').strip().lower() not in MISSING

def analyze(raw):
    text = raw.decode('utf-8-sig')
    first = text.splitlines()[0] if text.strip() else ''
    delimiter = '\t' if '\t' in first else ','
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = reader.fieldnames or []
    if len(headers) != len(set(headers)):
        raise ValueError('Duplicate column names are not supported.')
    if not {'genus', 'species'}.issubset(headers):
        raise ValueError('Include columns named genus and species. Coordinates are optional: decimalLatitude and decimalLongitude.')
    rows = []
    for record in reader:
        if None in record:
            raise ValueError('Some rows have more values than column headers. Check the CSV delimiter and quoting.')
        row = {k: (v or '').strip() for k, v in record.items()}
        row['review_status'] = ('Species named' if known(row['species']) else
                                'Needs species identification' if known(row['genus']) else
                                'Missing genus and species')
        try:
            lat, lon = float(row.get('decimalLatitude', '')), float(row.get('decimalLongitude', ''))
            valid = math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180
        except ValueError:
            lat, lon, valid = None, None, False
        row['valid_coordinates'] = valid
        row['latitude'], row['longitude'] = (lat, lon) if valid else (None, None)
        rows.append(row)
        if len(rows) > 100000:
            raise ValueError('Please use a file containing no more than 100,000 records.')
    if not rows:
        raise ValueError('This file contains headers but no records.')
    return rows

def export_csv(rows):
    if not rows:
        return b''
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    for row in rows:
        # Prevent spreadsheet formulas from executing when an exported CSV is opened.
        writer.writerow({k: "'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@')) else v for k, v in row.items()})
    return output.getvalue().encode('utf-8')
