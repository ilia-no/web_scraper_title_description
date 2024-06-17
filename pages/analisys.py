import pandas as pd
import streamlit as st
from io import BytesIO

import seaborn as sns
import matplotlib.pyplot as plt


def load_file(file):
    new_file = BytesIO()
    new_file.write(file.getvalue())
    new_file.seek(0)
    return new_file


def autopct_format(values):
    def my_format(pct):
        total = sum(values)
        val = int(round(pct*total/100.0))
        return '{p:.1f}%  ({v:d})'.format(p=pct, v=val)
    return my_format



st.title('Results Analisys')

st.subheader('Load results file to analisys')
csv_file = st.file_uploader("", type=['csv'])
if csv_file or st.session_state.get('analisys_df') is not None:
    if st.session_state.get('analisys_df') is None:
        df = pd.read_csv(load_file(csv_file))
        st.session_state['analisys_df'] = df

    df = st.session_state['analisys_df']
    st.text(f"Data loaded! Rows amount: {len(st.session_state['analisys_df'])}")
    st.dataframe(st.session_state['analisys_df'], height=200)


    st.title('Data analisys')

    st.subheader("Missing Meta Data")
    df_success = df[df['error'].isna()]

    tab1, tab2, tab3 = st.tabs(['Title & Description', 'Title', 'Description'])
    with tab1:
        filtered_df = df_success[df_success['title'].isna() & df_success['description'].isna()]

        s = pd.Series([len(filtered_df), len(df_success) - len(filtered_df)])
        # Create a pie chart using matplotlib
        fig, ax = plt.subplots()
        ax.pie(s, labels=['missing', 'exist'], autopct=autopct_format(s), startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        ax.set_title('Missing Title & Description')

        # Display the pie chart in Streamlit
        st.pyplot(fig)


    with tab2:
        nans_amount = df_success['title'].isna().sum()
        s = pd.Series([nans_amount, len(df_success) - nans_amount])
        # Create a pie chart using matplotlib
        fig, ax = plt.subplots()
        ax.pie(s, labels=['missing', 'exist'], autopct=autopct_format(s), startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        ax.set_title('Missing Title')

        # Display the pie chart in Streamlit
        st.pyplot(fig)

    with tab3:
        nans_amount = df_success['description'].isna().sum()
        s = pd.Series([nans_amount, len(df_success) - nans_amount])
        # Create a pie chart using matplotlib
        fig, ax = plt.subplots()
        ax.pie(s, labels=['missing', 'exist'], autopct=autopct_format(s), startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        ax.set_title('Missing Description')

        # Display the pie chart in Streamlit
        st.pyplot(fig)


    st.subheader('Errors')

    tab1, tab2 = st.tabs(['Errors Rate', 'Errors Types'])
    with tab1:
        nans_amount = df['error'].isna().sum()
        s = pd.Series([len(df) - nans_amount, nans_amount])
        # Create a pie chart using matplotlib
        fig, ax = plt.subplots()
        ax.pie(s, labels=['errors', 'success'], autopct=autopct_format(s), startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        ax.set_title("Errors - Success rate on pie chart")

        # Display the pie chart in Streamlit
        st.pyplot(fig)


    with tab2:
        st.text("Errors Types")
        s = df['error'].value_counts().reset_index()
        s.columns = ['Category', 'Counts']
        st.dataframe(s)

        s['Category'] = s['Category'].apply(lambda x: ' '.join(x.split(' ')[:2])).str.replace(':', '')
        s.loc[s['Category'].str.startswith('ReadTimeout', na=False), 'Category'] = 'ReadTimeout'

        fig, ax = plt.subplots()
        sns.barplot(x='Category', y='Counts', data=s, ax=ax)
        ax.set_title('Bar Plot of Error Types')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        ax.set_title("Errors Types on bar plot")

        # Display the bar plot in Streamlit
        st.pyplot(fig)