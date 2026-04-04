import pandas as pd
import numpy as np
import os

def generate_mock_data(output_path="data/mock_needs.csv"):
    np.random.seed(42)
    num_records = 20
    
    # Base location: San Francisco (approx)
    base_lat = 37.7749
    base_lon = -122.4194
    
    categories = ["Food", "Medical", "Shelter"]
    descriptions = [
        "Need immediate medical supplies for clinic.",
        "Food shortage in the local community center.",
        "Temporary shelter required for 10 families.",
        "Critical shortage of clean drinking water.",
        "Blankets and warm clothing needed.",
        "Emergency first aid kits required.",
        "School supplies for local children missing after disaster.",
        "Urgent request for antibiotics and bandages.",
        "Soup kitchen running low on staple foods.",
        "Tents needed to replace damaged housing."
    ]
    
    data = {
        "urgency": np.random.randint(1, 11, size=num_records),
        "category": np.random.choice(categories, size=num_records),
        "latitude": base_lat + np.random.uniform(-0.05, 0.05, size=num_records),
        "longitude": base_lon + np.random.uniform(-0.05, 0.05, size=num_records),
        "description": np.random.choice(descriptions, size=num_records)
    }
    
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Success! Generated {num_records} mock records at {output_path}")

if __name__ == "__main__":
    generate_mock_data()
