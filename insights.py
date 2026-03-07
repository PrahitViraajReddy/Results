import pandas as pd
try:
    df=pd.read_csv("results.csv")
except FileNotFoundError:
    exit(0)
print(df.head())
grades={'O':10,'A+':9,'A':8,'B+':7,'B':6,'C':5,'F':0,'Ab':0}
df['grade']=df['grade'].map(grades)

df['weightedpoints']=df['grade']*df['credits']
print(df.head())
summary=df.groupby(['rollNumber','name','branch']).agg({
    'weightedpoints':'sum',
    'credits':'sum',
    'total':'mean'
    }).reset_index()
print(summary)
summary['SGPA'] = summary.apply(
    lambda x: round(x['weightedpoints'] / x['credits'], 2) if x['credits'] > 0 else 0.0, 
    axis=1
)
print(summary['SGPA'])
