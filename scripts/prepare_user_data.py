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
    'Company Linkedin Url': 'social_media',
    'First Name': 'first_name',
    'Last Name': 'last_name',
    'Title': 'leader_role',
    'Person Linkedin Url': 'leader_social_media'
}

df = df.rename(columns=column_mapping)

# Drop duplicates by website to avoid processing the same company multiple times
# Some companies in the user's CSV are duplicated (e.g., Northwestern University, Deloitte)
df = df.drop_duplicates(subset=['website'])

# Combine First and Last name into leader_name
if 'first_name' in df.columns and 'last_name' in df.columns:
    df['leader_name'] = df['first_name'].fillna('') + ' ' + df['last_name'].fillna('')
    df['leader_name'] = df['leader_name'].str.strip()
else:
    df['leader_name'] = ''

# Keep only the columns we need (and ignore others)
cols_to_keep = [
    'company_name', 'website', 'email', 'phone', 'employees', 'revenue', 
    'location', 'social_media', 'leader_name', 'leader_role', 'leader_social_media'
]

# Ensure all target columns exist (fill missing with empty if needed)
for col in cols_to_keep:
    if col not in df.columns:
        df[col] = ''
        
final_df = df[cols_to_keep]

# Save to a clean CSV
final_df.to_csv('data/clean_user_companies.csv', index=False)
print(f"Cleaned and saved {len(final_df)} unique companies.")
