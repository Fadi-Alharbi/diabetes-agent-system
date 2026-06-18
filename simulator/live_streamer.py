import pandas as pd
import requests
import time
import sys

def stream_data(file_path, patient_id):
    print(f"Starting live stream for patient {patient_id} from {file_path}")
    print("Sending 1 reading every 2 seconds to simulate real-time CGM data...")
    df = pd.read_csv(file_path)
    
    # Send events first so the agent has context (simulating that the user logged these)
    # Actually, we don't need to send all events, just let the glucose stream run.
    
    for index, row in df.head(300).iterrows():
        payload = {
            "patient_id": patient_id,
            "timestamp": row['timestamp'],
            "glucose_value": float(row['glucose_value'])
        }
        
        try:
            response = requests.post("http://127.0.0.1:8000/glucose/stream", json=payload)
            if response.status_code == 200:
                print(f"[{row['timestamp']}] Sent glucose: {row['glucose_value']} mg/dL. AI Agents Analyzing...")
            else:
                print(f"Failed to send: {response.text}")
        except Exception as e:
            print(f"Connection error: {e}")
            
        time.sleep(2) # Send every 2 seconds

if __name__ == "__main__":
    stream_data("dataset_patient_A_high_carb.csv", "A")
