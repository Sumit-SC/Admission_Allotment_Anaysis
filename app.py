import streamlit as st
import pandas as pd

# css
# Add custom CSS to hide the GitHub icon
hide_github_icon = """
#GithubIcon {
  visibility: hidden;
}
#MainMenu {
  visibility: hidden;
}
"""
st.markdown(hide_github_icon, unsafe_allow_html=True)

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

def main():
    st.title("College Admission Analysis App")
    
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
        default_columns = ['ChoiceCodeDisplay', 'CollegeName', 'ST', 'Reservation Details']
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
            
            if st.checkbox(label=f"Show colleges for reservation type '{reservation_type}', marks '{user_marks}', category type '{marks_col}' from '{file.name}' for the selected location '{location}'"):
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

if __name__ == "__main__":
    main()
