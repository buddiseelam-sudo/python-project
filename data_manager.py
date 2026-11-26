"""Local CSV/JSON persistence, searching, and bulk-import validation."""
import csv, json, shutil
from pathlib import Path
from core import validate_record, enrich_record

FIELDS = ["id", "trip_name", "destination", "start_date", "end_date", "travelers",
          "transport", "stay", "food", "activities", "budget_limit", "notes",
          "created_at", "total_cost", "budget_status"]

class DataManager:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.data_dir / "trips.csv"
        self.json_path = self.data_dir / "trips.json"
        self._initialize()

    def _initialize(self):
        # Recover safely from absent/corrupt storage; seed realistic sample data on first run.
        if not self.csv_path.exists() and not self.json_path.exists():
            sample_csv = Path("data/sample_trips.csv")
            if sample_csv.exists():
                shutil.copyfile(sample_csv, self.csv_path)
            else:
                self._write_csv([])
        if not self.json_path.exists():
            self._write_json(self._read_csv())
        else:
            try:
                self._read_json()
            except (json.JSONDecodeError, OSError, TypeError):
                self._write_json(self._read_csv())

    def _read_csv(self):
        if not self.csv_path.exists():
            return []
        try:
            with self.csv_path.open("r", newline="", encoding="utf-8-sig") as f:
                return [self._normalize(row) for row in csv.DictReader(f)]
        except (OSError, csv.Error):
            return []

    def _read_json(self):
        with self.json_path.open("r", encoding="utf-8") as f:
            rows = json.load(f)
        if not isinstance(rows, list):
            raise ValueError("JSON storage must contain a list of records.")
        return [self._normalize(r) for r in rows]

    def load_records(self):
        try:
            return self._read_json()
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            records = self._read_csv()
            self._write_json(records)
            return records

    def _normalize(self, row):
        result = dict(row)
        for key in ("travelers",):
            try: result[key] = int(result.get(key) or 1)
            except (ValueError, TypeError): result[key] = 1
        for key in ("transport", "stay", "food", "activities", "budget_limit", "total_cost"):
            try: result[key] = float(result.get(key) or 0)
            except (ValueError, TypeError): result[key] = 0.0
        return result

    def _write_csv(self, records):
        with self.csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows([enrich_record(r) for r in records])

    def _write_json(self, records):
        with self.json_path.open("w", encoding="utf-8") as f:
            json.dump([enrich_record(r) for r in records], f, indent=2, ensure_ascii=False)

    def save_records(self, records):
        normalized = [enrich_record(r) for r in records]
        self._write_json(normalized)
        self._write_csv(normalized)

    def add_record(self, record):
        errors = validate_record(record)
        if errors:
            raise ValueError("\\n".join(errors))
        records = self.load_records()
        record = dict(record)
        record.setdefault("id", f"TRIP-{max([int(''.join(c for c in str(r.get('id','')) if c.isdigit()) or 0) for r in records] + [0]) + 1:04d}")
        record.setdefault("created_at", __import__("datetime").datetime.now().isoformat(timespec="seconds"))
        records.append(enrich_record(record))
        self.save_records(records)
        return record

    def delete_record(self, record_id):
        records = self.load_records()
        kept = [r for r in records if str(r.get("id")) != str(record_id)]
        self.save_records(kept)
        return len(records) - len(kept)

    def search(self, records, keyword="", destination="All", status="All"):
        found = []
        for r in records:
            text = " ".join(str(r.get(k, "")) for k in ("trip_name", "destination", "notes", "id")).lower()
            if keyword.lower() not in text: continue
            if destination != "All" and r.get("destination") != destination: continue
            enriched = enrich_record(r)
            if status != "All" and enriched["budget_status"] != status: continue
            found.append(enriched)
        return found

    def import_csv(self, uploaded_file):
        decoded = uploaded_file.read().decode("utf-8-sig")
        reader = csv.DictReader(decoded.splitlines())
        accepted, errors = [], []
        for line_no, row in enumerate(reader, start=2):
            row = self._normalize(row)
            row.setdefault("id", "")
            row.setdefault("created_at", "")
            row.setdefault("notes", "")
            problems = validate_record(row)
            if problems:
                errors.append({"row": line_no, "errors": "; ".join(problems)})
            else:
                accepted.append(enrich_record(row))
        if accepted:
            existing = self.load_records()
            next_num = max([int(''.join(c for c in str(r.get('id','')) if c.isdigit()) or 0) for r in existing] + [0])
            for r in accepted:
                next_num += 1
                r["id"] = f"TRIP-{next_num:04d}"
                r["created_at"] = r.get("created_at") or __import__("datetime").datetime.now().isoformat(timespec="seconds")
            self.save_records(existing + accepted)
        return len(accepted), errors
