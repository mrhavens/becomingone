import os
import sys
import time
from lightning_sdk import Studio, Machine

def main():
    print("Starting Orchestrator for Hardware Experiment...")
    
    user_id = os.environ.get("LIGHTNING_USER_ID")
    api_key = os.environ.get("LIGHTNING_API_KEY")
    if not user_id or not api_key:
        print("Error: Missing Lightning credentials in environment.")
        sys.exit(1)
        
    try:
        # 1. Initialize a new Studio
        studio_name = "becomingone-experiment"
        print(f"Creating Lightning Studio: {studio_name}")
        studio = Studio(name=studio_name)
        
        print("Starting Studio on L4 GPU instance...")
        studio.start(machine=Machine.L4)
        
        # 2. Upload the codebase
        print("Uploading becomingone package...")
        studio.upload_folder("/tmp/becomingone", "/teamspace/studios/this_studio/becomingone")
        
        # 3. Run the payload
        print("Executing Experiment Payload...")
        # Note: pip install -e .[ml] installs transformers, torch, etc.
        cmd = "cd /teamspace/studios/this_studio/becomingone && pip install -e .[ml] && pip install pandas transformers torch && python experiments/experiment_payload.py"
        studio.run(cmd)
        
        # 4. Download results
        print("Downloading Results...")
        studio.download_file("/teamspace/studios/this_studio/becomingone/experiment_results.csv", "/tmp/becomingone/experiments/experiment_results.csv")
        
        print("Experiment completed successfully.")
        
    except Exception as e:
        print(f"Error during orchestration: {e}")
        
    finally:
        print("Cleaning up Studio...")
        try:
            studio.stop()
            studio.delete()
            print("Studio deleted.")
        except Exception as e:
            print(f"Warning: Failed to delete studio: {e}")

if __name__ == "__main__":
    main()
