import pandas as pd

df = pd.read_csv("./users_data.csv")

import matplotlib.pyplot as plt

data = df['birth_month'].value_counts()
labels = data.index
sizes = data.values

plt.figure(figsize=(10, 7))
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
plt.title('Users Distribution by Birth Month')
plt.axis('equal')
plt.show()