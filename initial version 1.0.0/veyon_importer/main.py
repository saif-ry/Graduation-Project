import subprocess
import csv
from pathlib import Path


def fetch_data_from_api() -> list:
    """
    retrieve data API.
    """

    # --- Dummy function to simulate API data retrieval ---
    return [
        {"name": "ALBARAA", "ip": "192.168.0.176", "mac": ""},
        {"name": "RAYAN", "ip": "192.168.0.189", "mac": ""},
        {"name": "YAHYA", "ip": "192.168.0.25", "mac": ""},
    ]


def build_veyon_csv_file(location_name: str, json_file: list) -> Path:
    """
    Build a Veyon-compatible CSV file from dummy API data.
    Returns the path of the created CSV file.
    """

    # --- Determine the script's current directory ---
    current_dir = Path(__file__).parent

    # CSV will be created here
    csv_path = current_dir / f"{location_name}.csv"

    # --- Write CSV in Veyon format ---
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")

        # Computer entries
        for pc in json_file:
            writer.writerow([
                location_name,
                "Computer",
                pc.get("name", ""),
                pc.get("ip", ""),
                pc.get("mac", "")
            ])

    return csv_path


def run_cmd(cmd: str, label: str):
    """
    Run a CLI command and print formatted output.
    """
    print(f"=== RUN: {label} ===\n")

    # --- Execute the command ---
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"{label}: [OK]\n")
    else:
        print(f"{label}: ERROR (code {result.returncode})\n")
        if result.stdout.strip():
            print("STDOUT:")
            print(f"{result.stdout.strip()}\n")
        if result.stderr.strip():
            print("STDERR:")
            print(f"{result.stderr.strip()}\n")

    print(f"=== END: {label} ===\n")

 
def clear_location_and_computer(veyon_cli_path: str):
    """
    Clear all existing network objects in Veyon.
    """

    cmd = (
        f'"{veyon_cli_path}" networkobjects import "{csv_file}" '
        'format "%location%;%type%;%name%;%host%;%mac%"'
    )
    run_cmd(cmd, "CLEAR EXISTING NETWORK")


def import_csv_into_veyon(veyon_cli_path: str, csv_file: Path):
    """
    Import the CSV file into Veyon.
    """

    cmd = (
        f'"{veyon_cli_path}" networkobjects import "{csv_file}" '
        'format "%location%;%type%;%name%;%host%;%mac%"'
    )
    run_cmd(cmd, "IMPORT NEW STUDENTS")


if __name__ == "__main__":
    VEYON_CLI_PATH = r"C:\Program Files\Veyon\veyon-cli.exe"  # full path to veyon-cli
    LOCATION_NAME = "STUDENTS" # Veyon location name

    # 1) Get data from API
    fetch_json_file = fetch_data_from_api()

    # 2) Build Veyon compatible file (CSV format file)
    csv_file = build_veyon_csv_file(location_name=LOCATION_NAME, json_file=fetch_json_file)
    print(f"CSV file created at: {csv_file}\n")

    # 3) Clear existing Veyon network objects
    clear_location_and_computer(veyon_cli_path=VEYON_CLI_PATH)

    # 4) Import CSV into Veyon
    import_csv_into_veyon(veyon_cli_path=VEYON_CLI_PATH, csv_file=csv_file)
    