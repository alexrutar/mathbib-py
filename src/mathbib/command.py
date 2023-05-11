import sys
from xdg_base_dirs import xdg_data_home

from .index import list_records, generate_records_from_storage

def cli():
    if len(sys.argv) == 1:
        print("Must specify command!")
    else:
        match sys.argv[1]:
            case 'file':
                key, identifier = sys.argv[2].split(":")
                candidate = xdg_data_home() / "mathbib" / "files" / key / f"{identifier}.pdf"
                if candidate.exists():
                    print(candidate)

            case 'list':
                for record in list_records():
                    print(record)

            case 'refresh':
                generate_records_from_storage()
            case _:
                print(f"Invalid command '{sys.argv[1]}'")
