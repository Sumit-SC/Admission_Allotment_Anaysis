import streamlit as st
import pandas as pd
from fpdf import FPDF

# Add custom CSS to hide the GitHub icon
# Hide Streamlit's GitHub icon
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Function to load Excel files
def load_data(file):
    return pd.read_excel(file)

# Function to filter colleges based on location
def filter_colleges_by_location(data, location):
    if location:
        return data[data['CollegeName'].str.contains(location, case=False)]
    return data

# Function to filter colleges based on reservation type
def filter_colleges_by_reservation(data, reservation):
    return data[data['Reservation Details'].str.contains(reservation, case=False)]

# Function to filter colleges based on marks
def filter_colleges_by_marks(data, marks_col, marks):
    data[marks_col] = pd.to_numeric(data[marks_col], errors='coerce')
    return data[data[marks_col] <= marks]

# generate pdf
def generate_pdf(df, user_marks):
    # Sort DataFrame by marks column
    df_sorted = df.sort_values(by=df.columns[1], ascending=False)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Based on Marks: {user_marks}", ln=True, align="C")

    # Define column widths
    col_widths = [30, 20, 140]  # Adjust the widths as needed

    # Add table headers
    pdf.set_font("Arial", size=10)
    pdf.set_fill_color(200, 220, 255)
    for col, width in zip(df.columns, col_widths):
        pdf.cell(width, 5, str(col), 1, 0, "C", 1)
    pdf.cell(30, 5, "", 1, 0, "C")  # Adding blank cell for the extra column
    pdf.ln()

    # Add table data with word wrapping for college name
    pdf.set_font("Arial", size=10)  # Adjust font size for the third column
    for _, row in df_sorted.iterrows():
        for col, width in zip(df.columns, col_widths):
            if col == 'CollegeName':
                pdf.multi_cell(width, 5, str(row[col]), 1, "L")
            else:
                pdf.cell(width, 5, str(row[col]), 1, 0, "C")
        pdf.cell(30, 5, "", 1, 0, "C")  # Adding blank cell for the extra column
        pdf.ln()

    return pdf


def main():
    st.title("College Admission Prediction App using Previous Year Cut-Off")
    
    uploaded_files = st.file_uploader("Upload Excel files", type="xlsx", accept_multiple_files=True)
    
    if uploaded_files:
        # Load data from the first uploaded file
        first_file_data = load_data(uploaded_files[0])

        # Extract category names and reservation types from the first file
        excluded_columns = ['ChoiceCodeDisplay', 'CollegeName', 'Reservation Details']
        filtered_columns = [col for col in first_file_data.columns if col not in excluded_columns]
        reservation_types = first_file_data['Reservation Details'].unique()

        # User Inputs
        st.subheader("User Inputs")
        user_marks = st.number_input("Enter your marks", min_value=0, step=1)
        reservation_type = st.selectbox("Select the reservation type", reservation_types)
        marks_col = st.selectbox("Select the category column [Category type] :", filtered_columns)
        location = st.text_input("Enter location to filter colleges (leave empty to include all)", value="")

        # Columns to display
        st.subheader("Select Columns for Analysis")
        all_columns = first_file_data.columns.tolist()
        default_columns = ['ChoiceCodeDisplay', 'ST', 'CollegeName']
        selected_columns = st.multiselect("Select columns to display :", all_columns, default=default_columns)

        for i, file in enumerate(uploaded_files):
            # Load data for each file
            data = load_data(file)
            st.divider()
            st.header(f"Analysis for {file.name}")
            
            if st.checkbox(f"Show raw data for {file.name}"):
                st.dataframe(data)

            # Filter data based on user inputs
            filtered_location_colleges = filter_colleges_by_location(data, location)
            filtered_reservation_colleges = filter_colleges_by_reservation(filtered_location_colleges, reservation_type)
            filtered_colleges = filter_colleges_by_marks(filtered_reservation_colleges, marks_col, user_marks)
            
            if st.checkbox(label=f"Show colleges for reservation type {reservation_type} from {file.name}"):
                st.write(f"Colleges for reservation type {reservation_type}:")
                st.dataframe(filtered_reservation_colleges)

            if st.button(f"Filter Colleges for {file.name}"):
                st.write(f"Recommended colleges based on your marks ({user_marks}):")
                st.dataframe(filtered_colleges[selected_columns])

                # Additional Analysis
                st.write("Top 5 colleges based on marks:")
                st.write(filtered_colleges.nlargest(5, marks_col)[selected_columns])

                st.subheader("Additional Analysis")
                st.write(f"Distribution of marks in predicted colleges for your marks '{user_marks}':")
                st.write(filtered_colleges[marks_col].describe())

                # Save results to PDF
                pdf = generate_pdf(filtered_colleges[selected_columns], user_marks)
                pdf_output = f"College_Admission_Analysis_{file.name}.pdf"
                pdf.output(pdf_output)

                with open(pdf_output, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=pdf_output,
                        mime='application/pdf'
                    )

if __name__ == "__main__":
    main()