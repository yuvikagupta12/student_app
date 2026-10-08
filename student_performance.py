import streamlit as st
import pandas as pd

st.set_page_config(page_title="Student Performance Dashboard", layout="wide")

st.title("📊 Student Performance Dashboard")

# Let you upload your dataset
uploaded_file = st.sidebar.file_uploader("Upload student data (CSV)", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # 🔍 SIDEBAR FILTERS
    st.sidebar.header("Filter Options")
    
    # Create a copy of the dataframe to filter
    filtered_df = df.copy()
    
    # List of all available columns in your uploaded CSV
    all_columns = list(df.columns)
    
    # 1. DYNAMIC CATEGORICAL FILTER
    # Let the user pick WHICH column they want to filter by text/category
    selected_cat_col = st.sidebar.selectbox("Choose column to filter by:", ["None"] + all_columns)
    
    if selected_cat_col != "None":
        unique_vals = ["All"] + list(df[selected_cat_col].dropna().unique())
        selected_val = st.sidebar.selectbox(f"Select value for {selected_cat_col}:", unique_vals)
        if selected_val != "All":
            filtered_df = filtered_df[filtered_df[selected_cat_col] == selected_val]
            
    # 2. DYNAMIC NUMERIC FILTER
    # Find all columns that contain numbers (like scores, ages, IDs)
    numeric_cols = list(df.select_dtypes(include=['number']).columns)
    
    if numeric_cols:
        selected_num_col = st.sidebar.selectbox("Choose numeric column to filter:", ["None"] + numeric_cols)
        if selected_num_col != "None":
            min_val = float(df[selected_num_col].min())
            max_val = float(df[selected_num_col].max())
            
            if min_val < max_val:
                selected_range = st.sidebar.slider(
                    f"Select {selected_num_col} Range",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val)
                )
                filtered_df = filtered_df[
                    (filtered_df[selected_num_col] >= selected_range[0]) & 
                    (filtered_df[selected_num_col] <= selected_range[1])
                ]

    # 📈 METRICS (Calculated from the filtered data)
    st.subheader("Overview Metrics")
    col1, col2 = st.columns(2)
    col1.metric("Total Students (Filtered)", len(filtered_df))
    
    # Dynamically find a column named 'score' (case-insensitive) to calculate average
    score_col = next((col for col in df.columns if 'score' in col.lower()), None)
    
    if score_col and len(filtered_df) > 0:
        col2.metric(f"Average {score_col}", f"{filtered_df[score_col].mean():.2f}")
    else:
        col2.metric("Average Score", "N/A")
        
    # 📋 DATA TABLE DISPLAY
    st.subheader("📋 Student Records")
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("⚠️ No student records match the selected filters.")
        
else:
    st.info("💡 Please upload a student CSV file using the sidebar to view the dashboard metrics.")
