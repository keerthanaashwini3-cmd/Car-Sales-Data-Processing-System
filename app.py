import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Car Sales Data Processing System",
    page_icon="📊",
    layout="wide"
)

# ---------------- LOGIN ----------------

USERNAME = "admin"
PASSWORD = "car123"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("🚗 Car Sales Data Processing System")
    st.subheader("🔐 Secure Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input(
            "Password",
            type="password"
        )
        login = st.form_submit_button("Login")

    if login:
        if username == USERNAME and password == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Incorrect username or password.")

    st.stop()


# ---------------- SIDEBAR ----------------

st.sidebar.title("🚗 Car Sales Data Processing System")
st.sidebar.success("System Ready")

if st.sidebar.button("🔒 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Upload Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Choose Excel or CSV File",
    type=["xlsx", "xls", "csv"]
)


# ---------------- MAIN TITLE ----------------

st.title("🚗 Car Sales Data Processing System")
st.subheader("Data Analytics & Processing Dashboard")

st.write(
    "Upload any Excel or CSV dataset to preview, "
    "validate, clean, analyze, visualize and export data."
)

if uploaded_file is None:

    st.info("Upload your dataset using the sidebar.")

    st.markdown("""
    ### Available Features

    - Dataset Preview
    - Data Cleaning
    - Missing Value Analysis
    - Duplicate Checking
    - Search and Filtering
    - Automatic Charts
    - Data Quality Summary
    - CSV and Excel Export
    """)

    st.stop()


# ---------------- LOAD DATA ----------------

try:

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):

        try:
            df = pd.read_csv(uploaded_file)
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            df = pd.read_csv(
                uploaded_file,
                encoding="latin-1"
            )

    else:

        excel_file = pd.ExcelFile(uploaded_file)

        if len(excel_file.sheet_names) > 1:

            sheet_name = st.selectbox(
                "Select Excel Sheet",
                excel_file.sheet_names
            )

        else:
            sheet_name = excel_file.sheet_names[0]

        df = pd.read_excel(
            excel_file,
            sheet_name=sheet_name
        )

except Exception as error:

    st.error("Unable to read this file.")
    st.code(str(error))
    st.stop()


# ---------------- VALIDATE DATA ----------------

if df.empty or len(df.columns) == 0:

    st.error("The uploaded file contains no usable data.")
    st.stop()

df.columns = df.columns.astype(str).str.strip()

# Make duplicate column names unique
new_columns = []
column_counts = {}

for column in df.columns:

    column_counts[column] = column_counts.get(column, 0) + 1

    if column_counts[column] == 1:
        new_columns.append(column)
    else:
        new_columns.append(
            f"{column}_{column_counts[column]}"
        )

df.columns = new_columns

# Remove completely empty rows and columns
df = df.dropna(how="all")
df = df.dropna(axis=1, how="all")

if df.empty or len(df.columns) == 0:

    st.error("No usable data found in this file.")
    st.stop()


# ---------------- DATA CLEANING ----------------

original_rows = len(df)
original_columns = len(df.columns)

missing_before = int(df.isna().sum().sum())
duplicates_before = int(df.duplicated().sum())

clean_df = df.copy()

# Remove duplicate records
clean_df = clean_df.drop_duplicates()

# Standardize column names
clean_df.columns = clean_df.columns.str.strip()

# Replace missing values in text columns
for column in clean_df.select_dtypes(
    include=["object", "string"]
).columns:

    clean_df[column] = (
        clean_df[column]
        .replace(r"^\s*$", pd.NA, regex=True)
        .fillna("Not Available")
    )

# Fill missing numeric values with the median
for column in clean_df.select_dtypes(
    include="number"
).columns:

    if clean_df[column].isna().any():

        median_value = clean_df[column].median()

        if pd.notna(median_value):
            clean_df[column] = clean_df[column].fillna(
                median_value
            )

# Fill missing date values
for column in clean_df.select_dtypes(
    include=["datetime"]
).columns:

    clean_df[column] = clean_df[column].fillna(
        "Not Available"
    )

st.success("Dataset loaded and processed successfully!")

st.caption(f"Uploaded File: {uploaded_file.name}")


# ---------------- OVERVIEW ----------------

st.header("📌 Dataset Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Total Records",
    f"{len(df):,}"
)

c2.metric(
    "Total Columns",
    len(df.columns)
)

c3.metric(
    "Missing Values",
    f"{missing_before:,}"
)

c4.metric(
    "Duplicate Rows",
    f"{duplicates_before:,}"
)

st.markdown("---")


# ---------------- DATA PREVIEW ----------------

st.header("📋 Data Preview")

st.write("Showing the first 10 records.")

st.dataframe(
    df.head(10),
    width="stretch"
)

with st.expander("View Complete Dataset"):

    st.dataframe(
        df,
        width="stretch"
    )


# ---------------- SEARCH AND FILTER ----------------

st.header("🔍 Search and Filter")

filtered_df = clean_df.copy()

search_text = st.text_input(
    "Search across all columns"
)

if search_text.strip():

    search_mask = filtered_df.astype(str).apply(
        lambda column: column.str.contains(
            search_text,
            case=False,
            na=False,
            regex=False
        )
    ).any(axis=1)

    filtered_df = filtered_df[search_mask]


# Categorical filters
categorical_columns = filtered_df.select_dtypes(
    include=["object", "string", "category"]
).columns.tolist()

if categorical_columns:

    selected_column = st.selectbox(
        "Choose a column to filter",
        ["No Filter"] + categorical_columns
    )

    if selected_column != "No Filter":

        available_values = (
            filtered_df[selected_column]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_values = st.multiselect(
            f"Select {selected_column} values",
            available_values
        )

        if selected_values:

            filtered_df = filtered_df[
                filtered_df[selected_column]
                .astype(str)
                .isin(selected_values)
            ]

st.write(
    f"Filtered Records: {len(filtered_df):,}"
)

st.dataframe(
    filtered_df,
    width="stretch"
)


# ---------------- DATA QUALITY ----------------

st.header("✅ Data Quality Summary")

quality_df = pd.DataFrame({
    "Column Name": clean_df.columns,
    "Data Type": [
        str(dtype) for dtype in clean_df.dtypes
    ],
    "Missing Values": [
        int(value)
        for value in clean_df.isna().sum()
    ],
    "Unique Values": [
        int(clean_df[column].nunique())
        for column in clean_df.columns
    ]
})

st.dataframe(
    quality_df,
    width="stretch"
)

remaining_missing = int(clean_df.isna().sum().sum())
remaining_duplicates = int(clean_df.duplicated().sum())

total_cells = clean_df.shape[0] * clean_df.shape[1]

if total_cells > 0:

    quality_score = (
        1 - (
            remaining_missing + remaining_duplicates
        ) / total_cells
    ) * 100

    quality_score = max(
        0,
        min(100, quality_score)
    )

else:
    quality_score = 0

q1, q2, q3 = st.columns(3)

q1.metric(
    "Data Quality Score",
    f"{quality_score:.1f}%"
)

q2.metric(
    "Remaining Missing Values",
    remaining_missing
)

q3.metric(
    "Remaining Duplicates",
    remaining_duplicates
)


# ---------------- AUTOMATIC CHARTS ----------------

st.header("📈 Data Visualization")

numeric_columns = clean_df.select_dtypes(
    include="number"
).columns.tolist()

chart_categories = clean_df.select_dtypes(
    include=["object", "string", "category"]
).columns.tolist()

# Bar chart
if chart_categories:

    category_column = st.selectbox(
        "Choose a category for Bar Chart",
        chart_categories,
        key="bar_category"
    )

    top_categories = (
        clean_df[category_column]
        .astype(str)
        .value_counts()
        .head(10)
        .reset_index()
    )

    top_categories.columns = [
        category_column,
        "Count"
    ]

    fig_bar = px.bar(
        top_categories,
        x=category_column,
        y="Count",
        title=f"Top 10 Values in {category_column}"
    )

    st.plotly_chart(
        fig_bar,
        width="stretch"
    )

# Numeric chart
if numeric_columns:

    numeric_column = st.selectbox(
        "Choose a numeric column",
        numeric_columns
    )

    fig_hist = px.histogram(
        clean_df,
        x=numeric_column,
        title=f"Distribution of {numeric_column}"
    )

    st.plotly_chart(
        fig_hist,
        width="stretch"
    )

# Pie chart
if chart_categories:

    pie_column = st.selectbox(
        "Choose a column for Pie Chart",
        chart_categories,
        key="pie_category"
    )

    pie_data = (
        clean_df[pie_column]
        .astype(str)
        .value_counts()
        .head(10)
        .reset_index()
    )

    pie_data.columns = [
        pie_column,
        "Count"
    ]

    fig_pie = px.pie(
        pie_data,
        names=pie_column,
        values="Count",
        title=f"Distribution of {pie_column}"
    )

    st.plotly_chart(
        fig_pie,
        width="stretch"
    )

if not numeric_columns and not chart_categories:

    st.info(
        "Automatic charts are unavailable for these column types."
    )


# ---------------- NUMERIC SUMMARY ----------------

st.header("📊 Numerical Analysis")

if numeric_columns:

    st.dataframe(
        clean_df[numeric_columns].describe(),
        width="stretch"
    )

else:

    st.info(
        "No numeric columns are available for numerical analysis."
    )


# ---------------- EXPORT DATA ----------------

st.header("📥 Export Processed Data")

st.write(
    "Download the cleaned dataset in CSV or Excel format."
)

csv_data = clean_df.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="⬇️ Download CSV",
    data=csv_data,
    file_name="processed_data.csv",
    mime="text/csv"
)

excel_buffer = BytesIO()

try:

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        clean_df.to_excel(
            writer,
            index=False,
            sheet_name="Processed Data"
        )

    st.download_button(
        label="⬇️ Download Excel",
        data=excel_buffer.getvalue(),
        file_name="processed_data.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

except Exception as error:

    st.warning(
        "Excel export is unavailable. "
        "You can still download the CSV file."
    )


# ---------------- PROCESSING SUMMARY ----------------

st.header("⚙️ Processing Summary")

s1, s2, s3 = st.columns(3)

s1.metric(
    "Original Records",
    original_rows
)

s2.metric(
    "Processed Records",
    len(clean_df)
)

s3.metric(
    "Removed Duplicate Rows",
    original_rows - len(clean_df)
)

st.success(
    "Data processing and analysis completed successfully!"
)

st.markdown("---")

st.caption(
    "Car Sales Data Processing System | "
    "Developed by Keerthana | BCA Final Year Project"
)