import streamlit as st
import pandas as pd
from fpdf import FPDF

# Add custom CSS to hide the GitHub icon
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

# Function to generate PDF
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)  # Reduced font size for less space
        self.set_text_color(255, 0, 0)  # Red color for title
        self.cell(0, 10, self.title, 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 9)  # Reduced font size for less space
        self.set_text_color(0, 0, 0)  # Default black color for chapter title
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)  # Reduced line spacing

    def add_college_data(self, df, col_widths):
        self.set_font('Arial', 'B', 6.15)
        headers = df.columns.tolist() + ["Preference"]
        for header, width in zip(headers, col_widths):
            self.set_fill_color(200, 220, 255)
            self.cell(width, 10, str(header), 1, 0, 'C', fill=True)
        self.ln()

        self.set_font('Arial', '', 6.15)
        for row in df.itertuples(index=False):
            for value, width in zip(row, col_widths):
                if width == col_widths[-2]:  # For the last column (CollegeName), enable multi-cell for word wrapping
                    x, y = self.get_x(), self.get_y()
                    self.multi_cell(width, 10, str(value), 1)
                    self.set_xy(x + width, y)  # Set x to the right edge of the multicell
                else:
                    self.cell(width, 10, str(value), 1, 0, 'C')
            self.cell(col_widths[-1], 10, "", 1, 0, 'C')  # Adding blank cell for the Rank column
            self.ln()

def generate_pdf(df, user_marks, marks_col, filename, category_type, location, file_name):
    # Sort DataFrame by user selected marks column
    df_sorted = df.sort_values(by=marks_col, ascending=False)

    pdf = PDF()
    pdf.title = f"College Admission Analysis - {file_name}"  # Set the title for the header
    pdf.add_page()
    pdf.chapter_title(f"Prediction Based on Marks: '{user_marks}', Sorted by Category Type (marks): '{category_type}' based on Location provided '{location if location else 'All Locations'}'")
    
    # Define fixed column widths (adjust as needed)
    col_widths = [20, 10, 15, 140, 10]  # Adjust the widths as needed, ensuring last column is wider
    
    pdf.add_college_data(df_sorted, col_widths)
    pdf.output(filename)

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
        category_type = st.selectbox("Select the category column [Category type] :", filtered_columns)
        location = st.text_input("Enter location to filter colleges (leave empty to include all)", value="")
        # file_name = st.text_input("Enter a name for the analysis file (optional)", value="")

        # Columns to display
        st.subheader("Select Columns for Analysis")
        all_columns = first_file_data.columns.tolist()
        default_columns = ['ChoiceCodeDisplay', 'ST', 'General', 'CollegeName']
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
            filtered_colleges = filter_colleges_by_marks(filtered_reservation_colleges, category_type, user_marks)
            
            if st.checkbox(label=f"Show colleges for reservation type {reservation_type} from {file.name}"):
                st.write(f"Colleges for reservation type {reservation_type}:")
                st.dataframe(filtered_reservation_colleges)

            if st.button(f"Filter Colleges for {file.name}"):
                st.write(f"Recommended colleges based on your marks ({user_marks}):")
                st.dataframe(filtered_colleges[selected_columns])

                # Additional Analysis
                st.write("Top 5 colleges based on marks:")
                st.write(filtered_colleges.nlargest(5, category_type)[selected_columns])

                st.subheader("Additional Analysis")
                st.write(f"Distribution of marks in predicted colleges for your marks '{user_marks}':")
                st.write(filtered_colleges[category_type].describe())

                # Save results to PDF
                pdf_output = f"College_Admission_Analysis_{file.name}.pdf"
                generate_pdf(filtered_colleges[selected_columns], user_marks, category_type, pdf_output, category_type, location, file.name)

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