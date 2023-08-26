import csv
import pandas as pd
import streamlit as st
import tempfile
import base64
from io import BytesIO
import os
import plotly.express as px
import xlrd
import openpyxl
import plotly.graph_objects as go

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
        st.title("Expense Categorization App")
        st.write(f'Your expense.csv should have column names Date, Description, Debit and Credit. "Amount" Column can be used if Debit and Credit columns are not available')
        st.image("expense_example.png", use_column_width=True)
        
        st.write(f'Your category.csv should have the following column names: Keyword and Category. In addition, Keyword-Category pair has to be unique among the list, if duplicated pair/s are identified from the list, this program will run into error')
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

            df = pd.read_csv(expenses_file)
            df.fillna(0, inplace=True)  # Replace NaN values with zero

            header = df.columns.tolist()
            if 'Amount' not in header:
                header.append('Amount')
                has_amount = False
            else:
                has_amount = True

            header.append("Category")
            categorized_expenses.append(header)

            for index, row in df.iterrows():
                description = row['Description'].strip().lower()

                if not has_amount:
                    debit = pd.to_numeric(row['Debit'], errors='coerce')
                    credit = pd.to_numeric(row['Credit'], errors='coerce')
                    amount = debit + credit
                    row['Amount'] = amount

                category_found = False
                for keyword, category in category_mapping.items():
                    if keyword in description:
                        row['Category'] = category
                        categorized_expenses.append(row.tolist())
                        category_found = True
                        break
                if not category_found:
                    row['Category'] = "Uncategorized"
                    categorized_expenses.append(row.tolist())

            return categorized_expenses


        def main():
            
            # YouTube video ID (the string of characters after "v=" in the YouTube URL)
            video_id = "a7yLgMALYtw"
            
            # YouTube embed code
            youtube_embed_code = f"""
            <iframe width="330" height="200" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>
            """

            # File upload
            with st.sidebar:
                expenses_file = st.file_uploader("Upload Expenses CSV file", type=["csv"])
                category_file = st.file_uploader("Upload Category Mapping CSV file", type=["csv"])

                # Add content to the bar
                st.write("How to use this app")
                
                # Display the YouTube video
                st.components.v1.html(youtube_embed_code, height=330)

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
                expenses_df['Date'] = pd.to_datetime(expenses_df['Date'], infer_datetime_format=True, errors='coerce')


                category_mapping_df = pd.read_csv(temp_category_mapping.name)

                # Show uploaded files
                st.subheader("Uploaded Expenses CSV:")
                st.write(expenses_df)

                st.subheader("Uploaded Category Mapping CSV:")
                st.write(category_mapping_df)

                # Categorize expenses
                categorized_expenses = categorize_expenses(temp_expenses.name, temp_category_mapping.name)
                categorized_df = pd.DataFrame(categorized_expenses[1:], columns=categorized_expenses[0])
                categorized_df['Date'] = pd.to_datetime(categorized_df['Date'], infer_datetime_format=True, errors='coerce')
                
                ##### Draw bar chart by monthly categorized expense ###################################
                selected_category = st.selectbox("Select a category", categorized_df['Category'].unique(),index=2)

                if selected_category:
                    # Filter data for the selected category
                    category_df = categorized_df[categorized_df['Category'] == selected_category]
                    category_df['Date'] = pd.to_datetime(category_df['Date'])
                    category_df.fillna(0)

                    # Group by month and calculate total expenses
                    monthly_expenses = category_df.groupby(category_df['Date'].dt.to_period('M'))['Amount'].sum()

                    # Draw bar chart for month-to-month comparison
                    fig_bar = px.bar(x=monthly_expenses.index.astype(str), y=monthly_expenses.values)
                    fig_bar.update_layout(title="Month-to-Month Expense Comparison", xaxis_title="Month", yaxis_title = selected_category, xaxis_tickformat='%b' )


                    st.write(f'Total: {round(category_df["Amount"].sum(), 2)}')
                    st.write(category_df)
                    fig_bar.layout.xaxis.tickvals = pd.date_range('2023-01', '2023-12', freq='MS')
                    st.plotly_chart(fig_bar)
                    
                    #### monthly total expense bar chart  ###
                    categorized_df=categorized_df[~categorized_df['Description'].str.contains("AUTOPAY")]
                    total_monthly = categorized_df.groupby(categorized_df['Date'].dt.to_period('M'))['Amount'].sum()
                    
                    # Draw bar chart for month-to-month comparison
                    total_fig_bar = px.bar(x=total_monthly.index.astype(str), y=total_monthly.values)
                    total_fig_bar.update_layout(title="Month-to-Month Total Expense Comparison", xaxis_title="Month", yaxis_title="Total Expense", xaxis_tickformat='%b' )
                    total_fig_bar.layout.xaxis.tickvals = pd.date_range('2023-01', '2023-12', freq='MS')
                    st.plotly_chart(total_fig_bar)
                
                ######################################## Draw treemap   #####################
                # fig = px.treemap(categorized_df, path=['Category'], values='Amount', color='Amount',
                #                  color_continuous_scale='RdBu', title='Expense Amount by Category')
                
                # st.plotly_chart(fig)

                # Dropdown selector for categorizing the treemap by month
                category_by_month = st.selectbox("Categorize Treemap by Month:", ['All Periods'] + list(categorized_df['Date'].dt.to_period('M').unique()))
        
                # Modify the treemap title based on the selected month
                if category_by_month != 'All Periods':
                    filtered_categorized_df = categorized_df[categorized_df['Date'].dt.to_period('M') == category_by_month]
                    treemap_title = f'Expense Amount by Category for {category_by_month}'
                else:
                    filtered_categorized_df = categorized_df
                    treemap_title = 'Expense Amount by Category'
                
                #########SHOW TOTAL OF AMOUNT BY MONTH BUT EXCLUDE AUTOPAY CARD PAYMENT #################
                # Filter out rows with Description containing "AUTOPAY"
                filtered_categorized_df_no_autopay = filtered_categorized_df[~filtered_categorized_df['Description'].str.contains("AUTOPAY")]
                
                # Calculate the sum of the "Amount" column for the filtered DataFrame
                total_amount_no_autopay = filtered_categorized_df_no_autopay["Amount"].sum()
                
                st.write(f'Total (Excluding AUTOPAY): {round(total_amount_no_autopay, 2)}')
                ##########################################################################################
                
                # Create treemap
                fig = px.treemap(filtered_categorized_df, path=['Category'], values='Amount', title=treemap_title)
                st.plotly_chart(fig)

                # Show categorized expenses
                st.subheader("Categorized Expenses:")
                st.write(categorized_df)
                ###################################################################
                
                # Download categorized expenses as CSV
                st.markdown(get_table_download_link(categorized_df), unsafe_allow_html=True)

                # Delete temporary files
                os.remove(temp_expenses.name)
                os.remove(temp_category_mapping.name)

        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Sheet1')
            # writer.save()
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


