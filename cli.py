"""Required menu-driven terminal interface for the CampusSolve brief."""
from datetime import date
from data_manager import DataManager
from core import summarize, enrich_record

def ask_text(prompt):
    while True:
        value = input(prompt).strip()
        if value: return value
        print("This field cannot be blank. Try again.")

def ask_number(prompt, minimum=0, integer=False):
    while True:
        try:
            value = int(input(prompt)) if integer else float(input(prompt))
            if value >= minimum: return value
            print(f"Enter a value greater than or equal to {minimum}.")
        except ValueError:
            print("Enter a valid number.")

def add_trip(dm):
    from core import validate_record
    record = {
        "trip_name": ask_text("Trip name: "),
        "destination": ask_text("Destination: "),
        "start_date": ask_text("Start date (YYYY-MM-DD): "),
        "end_date": ask_text("End date (YYYY-MM-DD): "),
        "travelers": ask_number("Travelers: ", 1, True),
        "transport": ask_number("Transport cost: "),
        "stay": ask_number("Stay cost: "),
        "food": ask_number("Food cost: "),
        "activities": ask_number("Activity cost: "),
        "budget_limit": ask_number("Budget limit (0 if none): "),
        "notes": input("Notes (optional): ").strip()
    }
    errors = validate_record(record)
    if errors:
        print("Record not saved:")
        for error in errors: print(" -", error)
        return
    saved = dm.add_record(record)
    print(f"Saved {saved['id']} — estimated total ₹{saved['total_cost']:,.2f}")

def main():
    dm = DataManager()
    while True:
        print("\\n===== TRIP BUDGET CALCULATOR =====")
        print("1. Add trip\\n2. View all trips\\n3. Search trips\\n4. Executive summary\\n5. Exit")
        choice = input("Choose an option: ").strip()
        records = dm.load_records()
        if choice == "1": add_trip(dm)
        elif choice == "2":
            for r in records:
                e = enrich_record(r)
                print(f"{r.get('id')} | {r.get('trip_name')} | {r.get('destination')} | ₹{e['total_cost']:,.2f} | {e['budget_status']}")
        elif choice == "3":
            term = input("Search keyword: ").strip()
            for r in dm.search(records, term):
                print(f"{r.get('id')} | {r.get('trip_name')} | {r.get('destination')}")
        elif choice == "4":
            s = summarize(records)
            for key, value in s.items(): print(f"{key.replace('_',' ').title()}: {value}")
        elif choice == "5":
            print("Goodbye! Your data has been saved locally.")
            break
        else:
            print("Invalid menu choice. Select 1–5.")

if __name__ == "__main__":
    main()
