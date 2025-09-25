import json

with open("C:/Users/CHAMA COMPUTERS/Desktop/Data_Science/Academic/IRWA/Project/AgenticAI_project/Market_Researcher_AgenticAI/SocialMedia_Trend_Agent/cookies.json", "r", encoding="utf-8") as f:
    cookies_list = json.load(f)

# Convert list of dicts → single dict
cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies_list}

with open("cookies_fixed.json", "w", encoding="utf-8") as f:
    json.dump(cookies_dict, f, indent=2)

print("✅ Fixed cookies saved to cookies_fixed.json")