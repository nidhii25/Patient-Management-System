import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import uuid

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Patient Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    .main-header {
        padding: 1rem 0;
        border-bottom: 2px solid #e6f3ff;
        margin-bottom: 2rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin: 0;
    }
    .success-msg {
        padding: 0.5rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-msg {
        padding: 0.5rem;
        border-radius: 5px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9ff 0%, #e6f3ff 100%);
    }
</style>
""", unsafe_allow_html=True)


def fetch_patients():
    response = requests.get(f"{API_URL}/view")
    if response.status_code == 200:
        return response.json()
    return {}

if "patients" not in st.session_state:
    try:
        patients_data = fetch_patients()
        # Convert dict from backend (id: patient) → list of patients
        st.session_state.patients = list(patients_data.values())
    except Exception as e:
        st.session_state.patients = []
        st.error(f"⚠️ Failed to fetch patients: {e}")

def calculate_bmi(height, weight):
    return round(weight / (height ** 2), 2)

def get_bmi_verdict(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25:
        return "Normal"
    elif 25 <= bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def get_next_patient_id():
    if not st.session_state.patients:
        return 1
    return max(patient['id'] for patient in st.session_state.patients) + 1

def add_patient(patient_data):
    response = requests.post(f"{API_URL}/create", json=patient_data)
    return response.status_code == 201


def update_patient(patient_id, updated_data):
    response = requests.put(f"{API_URL}/edit/{patient_id}", json=updated_data)
    return response.status_code == 200


def delete_patient(patient_id):
    response = requests.delete(f"{API_URL}/delete/{patient_id}")
    return response.status_code == 200


def get_stats():
    patients = fetch_patients()
    if not patients:
        return {"total": 0, "avg_bmi": 0, "avg_age": 0, "male_count": 0, "female_count": 0}
    
    df = pd.DataFrame(patients.values())  # since API returns dict keyed by ID
    return {
        "total": len(df),
        "avg_bmi": round(df['bmi'].mean(), 1),
        "avg_age": round(df['age'].mean(), 1),
        "male_count": len(df[df['gender'] == 'male']),
        "female_count": len(df[df['gender'] == 'female'])
    }


# Header
st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🏥 Patient Management System")
st.markdown("**Manage patients, track health stats, and view BMI analysis**")
st.markdown('</div>', unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a page", [
    "🏠 Home",
    "➕ Add Patient", 
    "📋 View Patients",
    "✏️ Edit/Delete",
    "📊 Analytics",
    "ℹ️ About"
])

# HOME PAGE
if page == "🏠 Home":
    st.header("Dashboard Overview")
    
    # Get statistics
    stats = get_stats()
    
    # Display stats in cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value">👥 {stats['total']}</p>
            <p class="stat-label">Total Patients</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value">📊 {stats['avg_bmi']}</p>
            <p class="stat-label">Average BMI</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value">🎂 {stats['avg_age']}</p>
            <p class="stat-label">Average Age</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        gender_ratio = f"{stats['male_count']}M / {stats['female_count']}F"
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value">⚧️ {gender_ratio}</p>
            <p class="stat-label">Gender Split</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick action buttons
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("➕ Add New Patient", use_container_width=True):
            st.session_state.page = "➕ Add Patient"
            st.rerun()
    
    with col2:
        if st.button("📋 View All Patients", use_container_width=True):
            st.session_state.page = "📋 View Patients"
            st.rerun()

# ADD PATIENT PAGE
elif page == "➕ Add Patient":
    st.header("Add New Patient")
    
    patient_id = f"P{uuid.uuid4().hex[:4].upper()}"

    with st.form("add_form"):
        patient_id = st.text_input("Patient ID (e.g., P001)")   # <-- Added manual input
        name = st.text_input("Full Name")
        city = st.text_input("City")
        age = st.number_input("Age", min_value=1, max_value=120, step=1)
        gender = st.selectbox("Gender", ["male", "female", "other"])  # lowercase to match backend
        height = st.number_input("Height (m)", min_value=0.5, max_value=2.5, step=0.01)
        weight = st.number_input("Weight (kg)", min_value=1.0, max_value=200.0, step=0.1)

        submitted = st.form_submit_button("Add Patient")

    if submitted:
        if not patient_id:
            st.error("⚠️ Please enter a Patient ID.")
        else:
            patient_data = {
                "id": patient_id.strip(),   
                "name": name,
                "city": city,
                "age": age,
                "gender": gender,
                "height": height,
                "weight": weight
            }
            if add_patient(patient_data):    
                st.success(f"✅ Patient {patient_id} added successfully!")
                st.session_state.patients = list(fetch_patients().values())  
                st.rerun()

# VIEW PATIENTS PAGE
elif page == "📋 View Patients":
    st.header("All Patients")
    
    if not st.session_state.patients:
        st.info("No patients found. Add some patients first!")
    else:
        # Sort options
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            sort_by = st.selectbox("Sort by:", ["Name", "Age", "BMI", "Height", "Weight"])
        with col2:
            sort_order = st.selectbox("Order:", ["Ascending", "Descending"])
        with col3:
            search_id = st.number_input("Search by ID:", min_value=0, value=0)
        
        # Create dataframe
        df = pd.DataFrame(st.session_state.patients)
        
        # Filter by ID if specified
        if search_id > 0:
            df = df[df['id'] == search_id]
            if df.empty:
                st.warning(f"No patient found with ID: {search_id}")
        
        # Sort data
        if not df.empty:
            ascending = sort_order == "Ascending"
            sort_column = sort_by.lower()
            df = df.sort_values(by=sort_column, ascending=ascending)
            
            # Display table
            st.dataframe(
                df[['id', 'name', 'city', 'age', 'gender', 'height', 'weight', 'bmi', 'verdict']],
                column_config={
                    "id": "ID",
                    "name": "Name",
                    "city": "City",
                    "age": "Age",
                    "gender": "Gender",
                    "height": "Height (cm)",
                    "weight": "Weight (kg)",
                    "bmi": "BMI",
                    "verdict": "BMI Category"
                },
                use_container_width=True
            )

# EDIT/DELETE PAGE
elif page == "✏️ Edit/Delete":
    st.header("Edit or Delete Patient")
    
    if not st.session_state.patients:
        st.info("No patients available to edit or delete.")
    else:
        # Select patient
        patient_options = {f"{p['id']}: {p['name']}": p['id'] for p in st.session_state.patients}
        selected_patient_key = st.selectbox("Select Patient:", list(patient_options.keys()))
        selected_patient_id = patient_options[selected_patient_key]
        
        # Find selected patient
        selected_patient = next(p for p in st.session_state.patients if p['id'] == selected_patient_id)
        
        # Edit form
        st.subheader("Edit Patient Information")
        with st.form("edit_patient_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("Name", value=selected_patient['name'])
                new_city = st.text_input("City", value=selected_patient['city'])
                new_age = st.number_input("Age", min_value=1, max_value=120, value=selected_patient['age'])
            
            with col2:
                new_gender = st.selectbox("Gender", ["male", "female", "other"], 
                                        index=["male", "female", "other"].index(selected_patient['gender']))
                new_height = st.number_input("Height (m) *", min_value=0.0, max_value=5.0, value=1.7, step=0.1)
                new_weight = st.number_input("Weight (kg)", min_value=10.0, max_value=300.0, value=float(selected_patient['weight']))
            
            col1, col2 = st.columns(2)
            with col1:
                update_submitted = st.form_submit_button("Update Patient", use_container_width=True)
            with col2:
                delete_submitted = st.form_submit_button("Delete Patient", use_container_width=True, type="secondary")
            
            if update_submitted:
                updated_data = {
                    "name": new_name,
                    "city": new_city,
                    "age": new_age,
                    "gender": new_gender.lower(),
                    "height": new_height,
                    "weight": new_weight
                }
                
                if update_patient(selected_patient_id, updated_data):
                    st.success("✅ Patient updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update patient.")
            
            if delete_submitted:
                if delete_patient(selected_patient_id):
                    st.success("✅ Patient deleted successfully!")
                    st.session_state.patients = list(fetch_patients().values())
                    st.rerun()
                else:
                    st.error("❌ Failed to delete patient.")

# ANALYTICS PAGE
elif page == "📊 Analytics":
    st.header("Patient Analytics")
    
    if not st.session_state.patients:
        st.info("No data available for analytics. Add some patients first!")
    else:
        df = pd.DataFrame(st.session_state.patients)
        
        # Gender Distribution Pie Chart
        st.subheader("Gender Distribution")
        gender_counts = df['gender'].value_counts()
        fig_gender = px.pie(values=gender_counts.values, names=gender_counts.index, 
                           title="Patient Gender Distribution")
        st.plotly_chart(fig_gender, use_container_width=True)
        
        # BMI Category Distribution
        st.subheader("BMI Category Distribution")
        bmi_counts = df['verdict'].value_counts()
        colors = {'Underweight': '#3498db', 'Normal': '#2ecc71', 'Overweight': '#f39c12', 'Obese': '#e74c3c'}
        fig_bmi = px.bar(x=bmi_counts.index, y=bmi_counts.values,
                        title="Patients by BMI Category",
                        labels={'x': 'BMI Category', 'y': 'Number of Patients'},
                        color=bmi_counts.index,
                        color_discrete_map=colors)
        st.plotly_chart(fig_bmi, use_container_width=True)
        
        # Age Distribution
        st.subheader("Age Distribution")
        fig_age = px.histogram(df, x='age', nbins=10, title="Age Distribution of Patients",
                              labels={'age': 'Age', 'count': 'Number of Patients'})
        st.plotly_chart(fig_age, use_container_width=True)
        
        # BMI vs Age Scatter Plot
        st.subheader("BMI vs Age Analysis")
        fig_scatter = px.scatter(df, x='age', y='bmi', color='gender', size='weight',
                                title="BMI vs Age by Gender",
                                labels={'age': 'Age', 'bmi': 'BMI'})
        st.plotly_chart(fig_scatter, use_container_width=True)

# ABOUT PAGE
elif page == "ℹ️ About":
    st.header("About This System")
    
    st.markdown("""
    ### 🏥 Patient Management System
    
    This **Patient Management System** is a comprehensive healthcare application built with modern web technologies:
    
    #### 🛠️ Technology Stack
    - **Frontend**: Streamlit (Python-based web framework)
    - **Backend**: FastAPI (High-performance Python API framework)
    - **Data Visualization**: Plotly & Pandas
    - **Styling**: Custom CSS with healthcare-focused design
    
    #### ✨ Features
    - **CRUD Operations**: Create, Read, Update, and Delete patient records
    - **Health Analytics**: BMI calculation and categorization
    - **Data Visualization**: Interactive charts and graphs
    - **Search & Filter**: Find patients quickly
    - **Responsive Design**: Works on desktop and mobile devices
    
    #### 🎯 BMI Categories
    - **Underweight**: BMI < 18.5
    - **Normal**: BMI 18.5 - 24.9
    - **Overweight**: BMI 25.0 - 29.9
    - **Obese**: BMI ≥ 30.0
    
    #### 🔒 Data Security
    In a production environment, this system would include:
    - User authentication and authorization
    - Encrypted data storage
    - HIPAA compliance measures
    - Audit logging
    
    ---
    """
    )

    
    # System stats
    st.subheader("📊 Current System Status")
    stats = get_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Patients", stats['total'])
    with col2:
        st.metric("Average BMI", stats['avg_bmi'])
    with col3:
        st.metric("Average Age", stats['avg_age'])


     # Contact + credits
    st.markdown("""
    ---
    #### 📬 Contact
    - 🌐 [GitHub](https://github.com/yourusername)
    - 💼 [LinkedIn](https://www.linkedin.com/in/yourusername)
    - 📸 [Instagram](https://www.instagram.com/yourusername)

    **Built with ❤️ using Python, Streamlit, and FastAPI**

    *Version 1.0 - Healthcare Management Solution*
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 1rem;'>"
    "🏥 Patient Management System | Built with Streamlit & FastAPI"
    "</div>", 
    unsafe_allow_html=True
)