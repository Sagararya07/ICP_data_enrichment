import pandas as pd

# Read the raw user data
df = pd.read_csv('data/user_data.csv')

# Map columns to what load_csv.py expects
column_mapping = {
    'Company Name': 'company_name',
    'Website': 'website',
    'Email': 'email',
    'Corporate Phone': 'phone',
    '# Employees': 'employees',
    'Annual Revenue': 'revenue',
    'City': 'location',
    'Company Linkedin Url': 'social_media'
}

df = df.rename(columns=column_mapping)

# Drop duplicates by website to avoid processing the same company multiple times
# Some companies in the user's CSV are duplicated (e.g., Northwestern University, Deloitte)
df = df.drop_duplicates(subset=['website'])

# Keep only the columns we need (and ignore others)
cols_to_keep = list(column_mapping.values())
# Ensure all target columns exist (fill missing with empty if needed)
for col in cols_to_keep:
    if col not in df.columns:
        df[col] = ''
        
final_df = df[cols_to_keep]

# Save to a clean CSV
final_df.to_csv('data/clean_user_companies.csv', index=False)
print(f"Cleaned and saved {len(final_df)} unique companies.")
