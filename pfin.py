import csv
import pandas as pd
import streamlit as st
import tempfile
import base64
from io import BytesIO
import os
import plotly.express as px
import xlrd

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)


name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    if username == 'guest':
        try:
            if authenticator.register_user('Register user', preauthorization=False):
                    st.write('Please logout and log back in')
                    
        except Exception as e:
            st.error(e)
        with open('config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
        authenticator.logout('Logout', 'main', key='unique_key')
        
    else:        
        authenticator.logout('Logout', 'main', key='unique_key')
    
        st.write(f'Welcome *{name}*')
        
        st.write(f'your expense.csv should have the following column names and orders')
        st.image("expense_example.png", use_column_width=True)
        
        st.write(f'your category.csv should have the following column names and orders and the keyword has to be unique')
        st.image("category_example.png", use_column_width=True)
        
        
        def load_category_mapping(file_path):
            category_mapping = {}
            with open(file_path, 'r') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row
                for row in reader:
                    keyword = row[0].strip().lower()
                    category = row[1].strip()
                    category_mapping[keyword] = category
            return category_mapping

        def categorize_expenses(expenses_file, category_mapping_file):
            category_mapping = load_category_mapping(category_mapping_file)
            categorized_expenses = []

            with open(expenses_file, 'r') as expenses:
                reader = csv.reader(expenses)
                header = next(reader)
                header.append("Category")
                categorized_expenses.append(header)

                for row in reader:
                    description = row[2].strip().lower()
                    category_found = False
                    for keyword, category in category_mapping.items():
                        if keyword in description:
                            row.append(category)
                            categorized_expenses.append(row)
                            category_found = True
                            break
                    if not category_found:
                        row.append("Uncategorized")
                        categorized_expenses.append(row)

            return categorized_expenses

        def save_categorized_expenses(categorized_expenses, output_file):
            with open(output_file, 'w', newline='') as output:
                writer = csv.writer(output)
                writer.writerows(categorized_expenses)

            print(f"Categorized expenses saved to {output_file}")

        def main():
            st.title("Expense Categorization")

            # File upload
            with st.sidebar:
                expenses_file = st.file_uploader("Upload Expenses CSV file", type=["csv"])
                category_file = st.file_uploader("Upload Category Mapping CSV file", type=["csv"])


            if expenses_file is not None and category_file is not None:
                # Create temporary files
                temp_expenses = tempfile.NamedTemporaryFile(delete=False)
                temp_category_mapping = tempfile.NamedTemporaryFile(delete=False)

                # Save uploaded files to temporary files
                temp_expenses.write(expenses_file.read())
                temp_category_mapping.write(category_file.read())

                # Close and flush the temporary files
                temp_expenses.close()
                temp_category_mapping.close()

                expenses_df = pd.read_csv(temp_expenses.name)
                category_mapping_df = pd.read_csv(temp_category_mapping.name)

                # Show uploaded files
                st.subheader("Uploaded Expenses CSV:")
                st.write(expenses_df)

                st.subheader("Uploaded Category Mapping CSV:")
                st.write(category_mapping_df)

                # Categorize expenses
                categorized_expenses = categorize_expenses(temp_expenses.name, temp_category_mapping.name)
                categorized_df = pd.DataFrame(categorized_expenses[1:], columns=categorized_expenses[0])

                # Show categorized expenses
                st.subheader("Categorized Expenses:")
                st.write(categorized_df)

                # Get unique categories
                categories = categorized_df['Category'].unique()

                # Draw treemap
                fig = px.treemap(categorized_df, path=['Category'], values='Debit', color='Debit', hover_data=['Description'])
                fig.update_layout(title="Expense Treemap")
                st.plotly_chart(fig)

                # Select a category
                selected_category = st.selectbox("Select a category", categories)

                if selected_category:
                    # Filter data for the selected category
                    category_df = categorized_df[categorized_df['Category'] == selected_category]
                    category_df['Date'] = pd.to_datetime(category_df['Date'])
                    category_df.fillna(0)

                    category_df['Debit']=pd.to_numeric(category_df['Debit'])

                    # Group by month and calculate total expenses
                    monthly_expenses = category_df.groupby(category_df['Date'].dt.to_period('M'))['Debit'].sum()

                    # Draw bar chart for month-to-month comparison
                    fig_bar = px.bar(x=monthly_expenses.index.astype(str), y=monthly_expenses.values)
                    fig_bar.update_layout(title="Month-to-Month Expense Comparison", xaxis_title="Month", yaxis_title="Total Expense", xaxis_tickformat='%b' )


                    st.write(f'Total: {round(category_df["Debit"].sum(), 2)}')
                    st.write(category_df)
                    # st.write(monthly_expenses.index)
                    st.plotly_chart(fig_bar)





                # Download categorized expenses as CSV
                st.markdown(get_table_download_link(categorized_df), unsafe_allow_html=True)

                # Delete temporary files
                os.remove(temp_expenses.name)
                os.remove(temp_category_mapping.name)

        def to_excel(df):
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Sheet1')
            writer.save()
            processed_data = output.getvalue()
            return processed_data

        def get_table_download_link(df):
            """Generates a link allowing the data in a given panda dataframe to be downloaded
            in:  dataframe
            out: href string
            """
            val = to_excel(df)
            b64 = base64.b64encode(val)  # val looks like b'...'
            return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="download.xlsx">Download excel file</a>' # decode b'abc' => abc

        if __name__ == "__main__":
            main()
        
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password  \nIf you do not have one, login as guest, passcode is 5566')


