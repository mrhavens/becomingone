import os
from lightning_sdk import Studio

def main():
    try:
        print("=== Lightning AI Audit ===")
        print(f"USER_ID: {os.environ.get('LIGHTNING_USER_ID')}")
        
        studios = Studio.list()
        print(f"\nFound {len(studios)} Studios:")
        for s in studios:
            print(f"- {s.name} (Status: {s.status})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
