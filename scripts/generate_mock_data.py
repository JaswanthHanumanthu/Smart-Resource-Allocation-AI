import pandas as pd
import numpy as np
import os
import random

def generate_mock_data(output_path="data/mock_needs.csv"):
    np.random.seed(42)
    random.seed(42)
    num_records = 20
    
    base_lat = 37.7749
    base_lon = -122.4194
    
    categories = ["Food", "Medical", "Shelter", "General"]
    
    needs_data = [
        {"category": "Medical", "description": "Urgent need for insulin supplies at community health center. 30 diabetic patients at risk.", "urgency": 9, "people_affected": 30, "human_context_summary": "Elderly patients with diabetes requiring daily insulin injections."},
        {"category": "Food", "description": "Food bank completely empty. 200 families need emergency food rations.", "urgency": 8, "people_affected": 200, "human_context_summary": "Low-income families relying on food bank for daily meals."},
        {"category": "Shelter", "description": "Temporary shelter needed for 15 homeless individuals during rainstorm.", "urgency": 9, "people_affected": 15, "human_context_summary": "Homeless individuals exposed to severe weather conditions."},
        {"category": "Medical", "description": "First aid kits running low at community center. Minor injuries going untreated.", "urgency": 6, "people_affected": 45, "human_context_summary": "General community members with minor cuts and bruises."},
        {"category": "Food", "description": "School lunch program lacking supplies. 150 children may go hungry.", "urgency": 7, "people_affected": 150, "human_context_summary": "School children from low-income families dependent on school meals."},
        {"category": "Shelter", "description": "Damaged roof causing leaks. 8 families need temporary housing repairs.", "urgency": 5, "people_affected": 40, "human_context_summary": "Families living in partially damaged housing units."},
        {"category": "Medical", "description": "Shortage of hypertension medication at local clinic.", "urgency": 8, "people_affected": 60, "human_context_summary": "Elderly residents with chronic hypertension requiring daily medication."},
        {"category": "Food", "description": "Clean drinking water contaminated. Residents need bottled water.", "urgency": 9, "people_affected": 500, "human_context_summary": "Entire neighborhood affected by water contamination."},
        {"category": "General", "description": "Power outage affecting 30 households. Need generators.", "urgency": 6, "people_affected": 120, "human_context_summary": "Families without electricity during heatwave."},
        {"category": "Medical", "description": "Expectant mothers lacking prenatal vitamins and supplements.", "urgency": 7, "people_affected": 12, "human_context_summary": "Pregnant women in their second and third trimester."},
        {"category": "Shelter", "description": "Winter coats and blankets needed for 50 elderly residents.", "urgency": 6, "people_affected": 50, "human_context_summary": "Elderly residents without proper winter clothing."},
        {"category": "Food", "description": "Soup kitchen needing instant noodles and canned goods.", "urgency": 5, "people_affected": 80, "human_context_summary": "Homeless individuals and low-income families relying on soup kitchen."},
        {"category": "Medical", "description": "Dental emergency kits needed for mobile dental unit.", "urgency": 4, "people_affected": 25, "human_context_summary": "Underserved community with limited dental care access."},
        {"category": "General", "description": "Community center needs cleaning supplies for hygiene kits.", "urgency": 3, "people_affected": 100, "human_context_summary": "General community members benefiting from hygiene education."},
        {"category": "Shelter", "description": "Wheelchair-accessible van needed for disabled veteran transport.", "urgency": 7, "people_affected": 8, "human_context_summary": "Disabled veterans requiring transportation to medical appointments."},
        {"category": "Food", "description": "Baby formula and diapers needed for 20 infants.", "urgency": 8, "people_affected": 20, "human_context_summary": "New mothers unable to afford basic infant supplies."},
        {"category": "Medical", "description": "Mental health counseling services needed for trauma survivors.", "urgency": 7, "people_affected": 35, "human_context_summary": "Disaster survivors experiencing PTSD and anxiety."},
        {"category": "General", "description": "翻译：需要帮助老年人获取药物 (Translation: Elderly need help accessing medications)", "urgency": 6, "people_affected": 18, "human_context_summary": "Chinese-speaking elderly with language barrier to healthcare."},
        {"category": "Food", "description": "Vegetarian meal options urgently needed for temple community.", "urgency": 4, "people_affected": 60, "human_context_summary": "Vegetarian community members with dietary restrictions."},
        {"category": "Medical", "description": "Pet food needed for evacuees who brought animals. 12 families with pets.", "urgency": 3, "people_affected": 12, "human_context_summary": "Families refusing evacuation without pet accommodations."},
    ]
    
    data = {
        "urgency": [],
        "category": [],
        "latitude": [],
        "longitude": [],
        "description": [],
        "detected_language": ["English"] * num_records,
        "people_affected": [],
        "human_context_summary": [],
        "status": ["Pending"] * num_records,
        "verified": [True] * num_records,
        "report_count": [1] * num_records,
    }
    
    for i, need in enumerate(needs_data):
        data["urgency"].append(need["urgency"])
        data["category"].append(need["category"])
        data["latitude"].append(base_lat + random.uniform(-0.08, 0.08))
        data["longitude"].append(base_lon + random.uniform(-0.08, 0.08))
        data["description"].append(need["description"])
        data["people_affected"].append(need["people_affected"])
        data["human_context_summary"].append(need["human_context_summary"])
    
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Success! Generated {num_records} mock records at {output_path}")
    print(df.head())

if __name__ == "__main__":
    generate_mock_data()
