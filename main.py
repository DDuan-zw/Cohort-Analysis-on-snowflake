import streamlit as st
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import datetime as dt
# Snowpark for Python
from snowflake.snowpark.session import Session
from snowflake.snowpark.types import IntegerType, StringType, StructType, FloatType, StructField, DateType, Variant
from snowflake.snowpark.functions import udf, sum, col,array_construct,month,year,call_udf,lit,count
from snowflake.snowpark.version import VERSION
# Misc
import json
import logging 

# The code below is for the title and logo for this page.
st.set_page_config(page_title="Cohort Analysis on the Bikes dataset", page_icon="🚲")
bg_image = '''
<style>
[data-testid="stAppViewContainer"]{
background-image: url(https://lp-cms-production.imgix.net/2022-01/GettyRF_475680439.jpg?auto=format&q=75&w=1920);
backgroud-size:cover;
}

[data-testid="stHeader"]{
background-color: rgba(0,0,0,0);
}

[data-testid="stToolbar"]{
right : 2rem;}

</style>
'''
#st.markdown(bg_image, unsafe_allow_html=True)
#st.set_page_config(layout="wide")
st.sidebar.markdown("# Bike Cohort Analysis")
st.image(
    "TrevelBike.jpeg",
    #width  = 160
    use_column_width = True,
)

st.title("Cohort Analysis → `Bikes` dataset")

st.write("")

st.markdown(
    """

    This demo is inspired by this [Cohort Analysis Tutorial](https://github.com/maladeep/cohort-retention-rate-analysis-in-python).

"""
)

with st.expander("About this app"):

    st.write("")

    st.markdown(
        """
    ### 1.Dataset
    This dataset comes from the hypothetical KPMG.
    We focus on transaction sheet to be dataset for cohort analysis use.
    Objective: Find customer transaction retention funnel.
    Each row in the dataset contains information about an individual bike purchase:
    
    - Who bought it
    - How much they paid
    - The bike's `brand` and `product line`
    - Its `class` and `size`
    - What day the purchase happened
    - The day the product was first sold
    """
    )

    st.write("")

    st.markdown(
        """
    ### 2. Objective:
    The underlying code groups those purchases into cohorts and calculates the `retention rate` (split by month) so that one can answer the question:

    *if I'm making monthly changes to my store to get people to come back and buy more bikes, are those changes working?"*

    These cohorts are then visualized and interpreted through a heatmap [powered by Plotly](https://plotly.com/python/).

    """
    )

    st.write("")

# A function that will parse the date Time based cohort:  1 day of month
def get_month(x):
    return dt.datetime(x.year, x.month, 1)

@st.cache_resource
def connect2snowflake():
    # set logger
    logger = logging.getLogger("snowflake.snowpark.session")
    logger.setLevel(logging.ERROR)
    # Create Snowflake Session object
    connection_parameters = json.load(open('connection.json'))
    session = Session.builder.configs(connection_parameters).create()
    session.sql_simplifier_enabled = True

    snowflake_environment = session.sql('select current_user(), current_role(), current_database(), current_schema(), current_version(), current_warehouse()').collect()
    snowpark_version = VERSION
    return session
session = connect2snowflake()

@st.cache_data
def load_data():

    # Load data
    transaction_df = pd.DataFrame(session.table('TRANSACTIONS').collect())

    #transaction_df = session.sql('select * from TRANSACTIONS').toPandas()
    transaction_df.columns = [x.lower() for x in transaction_df.columns]
#-----Bing Start: New Column Profit------
    transaction_df['profit'] = transaction_df['list_price'] - transaction_df['standard_cost']
#-----Bing End: New Column Profit------

    # Process data
    transaction_df = transaction_df.replace(" ", np.NaN)
    transaction_df = transaction_df.fillna(transaction_df.mean())
    transaction_df["TransactionMonth"] = transaction_df["transaction_date"].apply(
        get_month
    )
    transaction_df["TransactionYear"] = transaction_df["transaction_date"].dt.year
    transaction_df["TransactionMonth"] = transaction_df["transaction_date"].dt.month
    for col in transaction_df.columns:
        if transaction_df[col].dtype == "object":
            transaction_df[col] = transaction_df[col].fillna(
                transaction_df[col].value_counts().index[0]
            )

    # Create transaction_date column based on month and store in TransactionMonth
    transaction_df["TransactionMonth"] = transaction_df["transaction_date"].apply(
        get_month
    )
    # Grouping by customer_id and select the InvoiceMonth value
    grouping = transaction_df.groupby("customer_id")["TransactionMonth"]
    # Assigning a minimum InvoiceMonth value to the dataset
    transaction_df["CohortMonth"] = grouping.transform("min")

    return transaction_df


transaction_df = load_data()

with st.expander("Show the `Bikes` dataframe"):
    st.write(transaction_df)


def get_date_int(df, column):
    year = df[column].dt.year
    month = df[column].dt.month
    day = df[column].dt.day
    return year, month, day


# Getting the integers for date parts from the `InvoiceDay` column
transcation_year, transaction_month, _ = get_date_int(
    transaction_df, "TransactionMonth"
)
# Getting the integers for date parts from the `CohortDay` column
cohort_year, cohort_month, _ = get_date_int(transaction_df, "CohortMonth")
#  Get the  difference in years
years_diff = transcation_year - cohort_year
# Calculate difference in months
months_diff = transaction_month - cohort_month

# Extract the difference in months from all previous values "+1" in addeded at the end so that first month is marked as 1 instead of 0 for easier interpretation. """
transaction_df["CohortIndex"] = years_diff * 12 + months_diff + 1

dtypes = transaction_df.dtypes.astype(str)
# Show dtypes
# dtypes

#-----Bing Start: Modify new_slider_01------
transaction_df_new_slider_01 = transaction_df[["brand", "product_line","online_order"]]
#-----Bing End: Modify new_slider_01--------
new_slider_01 = [col for col in transaction_df_new_slider_01]


#----Bing Start: Add Profit------
transaction_df_new_slider_02 = transaction_df[["list_price", "standard_cost","profit"]]
new_slider_02 = [col for col in transaction_df_new_slider_02]
#----Bing End: Add Profit------

st.write("")

cole, col1, cole, col2, cole = st.columns([0.1, 1, 0.05, 1, 0.1])

with col1:

    MetricSlider01 = st.selectbox("Pick your 1st metric", new_slider_01)

    MetricSlider02 = st.selectbox("Pick your 2nd metric", new_slider_02, index=1)
      

    st.write("")

with col2:

    if MetricSlider01 == "brand":
        # col_one_list = transaction_df_new["brand"].tolist()
        col_one_list = transaction_df_new_slider_01["brand"].drop_duplicates().tolist()
        multiselect = st.multiselect(
            "Select the value(s)", col_one_list, ["Solex", "Trek Bicycles"]
        )
        transaction_df = transaction_df[transaction_df["brand"].isin(multiselect)]

    elif MetricSlider01 == "product_line":
        col_one_list = (
            transaction_df_new_slider_01["product_line"].drop_duplicates().tolist()
        )
        multiselect = st.multiselect(
            "Select the value(s)", col_one_list, ["Standard", "Road"]
        )
        transaction_df = transaction_df[
            transaction_df["product_line"].isin(multiselect)
        ]
#------Bing Start: Add Online Order to MetricSlider01------
    if MetricSlider01 == "online_order":
        col_one_list = (
            transaction_df_new_slider_01["online_order"].drop_duplicates().tolist()
        )
        Online_CheckBox = st.checkbox('Online Order')
        Offline_CheckBox = st.checkbox('Offline Order')
        
        if Online_CheckBox and not Offline_CheckBox:
            Online_Selection = [0]
        if not Online_CheckBox and Offline_CheckBox:
            Online_Selection = [1]
        
        if (Online_CheckBox and Offline_CheckBox) or (not Online_CheckBox and not Offline_CheckBox):
            Online_Selection = [0,1]
        transaction_df = transaction_df[
        transaction_df["online_order"].isin(Online_Selection)
    ]
        
#------Bing End: Add Online Order to MetricSlider01------
        

#------Bing Start: Add Profit to MetricSlider02------
    if MetricSlider02 == "list_price":
        list_price_slider = st.slider(
            "List price (in $)", step=1, min_value=12, max_value=2091
        )
        transaction_df = transaction_df[
            transaction_df["list_price"] > list_price_slider
        ]

    elif MetricSlider02 == "standard_cost":
        standard_cost_slider = st.slider(
            "Standard cost (in $)", step=1, min_value=7, max_value=1759
        )
        transaction_df = transaction_df[
            transaction_df["list_price"] > standard_cost_slider
        ]
        
    elif MetricSlider02 == "profit":
        standard_cost_slider = st.slider(
        "Profit (in $)", step=1, min_value= -540, max_value= 1700
        )
        transaction_df = transaction_df[
            transaction_df["profit"] > standard_cost_slider
        ]
#------Bing End: Add Profit to MetricSlider02------
        
try:

    # Counting daily active user from each chort
    grouping = transaction_df.groupby(["CohortMonth", "CohortIndex"])
    # Counting number of unique customer Id's falling in each group of CohortMonth and CohortIndex
    cohort_data = grouping["customer_id"].apply(pd.Series.nunique)
    cohort_data = cohort_data.reset_index()
    # Assigning column names to the dataframe created above
    cohort_counts = cohort_data.pivot(
        index="CohortMonth", columns="CohortIndex", values="customer_id"
    )

    cohort_sizes = cohort_counts.iloc[:, 0]
    retention = cohort_counts.divide(cohort_sizes, axis=0)
    # Coverting the retention rate into percentage and Rounding off.
    retention = retention.round(3) * 100
    retention.index = retention.index.strftime("%Y-%m")

    # Plotting the retention rate
    fig = go.Figure()

    fig.add_heatmap(
        # x=retention.columns, y=retention.index, z=retention, colorscale="cividis"
        x=retention.columns,
        y=retention.index,
        z=retention,
        # Best
        # colorscale="Aggrnyl",
        colorscale="Bluyl",
    )

    fig.update_layout(title_text="Monthly cohorts showing retention rates", title_x=0.2)
    fig.layout.xaxis.title = "Cohort Group"
    fig.layout.yaxis.title = "Cohort Period"
    fig["layout"]["title"]["font"] = dict(size=25)
    fig.layout.width = 750
    fig.layout.height = 750
    fig.layout.xaxis.tickvals = retention.columns
    fig.layout.yaxis.tickvals = retention.index
    fig.layout.plot_bgcolor = "#efefef"  # Set the background color to white
    fig.layout.margin.b = 100
    fig

except IndexError:
    st.warning("This is throwing an exception, bear with us!")
