import pandas as pd
import re
import streamlit as st


def preprocess(data):
    # Apply the same regex processing
    pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s'
    messages = re.split(pattern, data)[1:]
    
    # Extract dates
    dates = re.findall(pattern, data)
    
    # Create DataFrame with user messages and dates
    df = pd.DataFrame({'user_message': messages, 'message_date': dates})
    
    # Convert message_date type
    df['message_date'] = df['message_date'].str.strip()
    df['message_date'] = pd.to_datetime(df['message_date'], format='%d/%m/%y, %H:%M -')
    df.rename(columns={'message_date': 'date'}, inplace=True)
    
    # Extract users and message content
    users = []
    messages = []
    for message in df['user_message']:
        entry = re.split(r'([\w\W]+?):\s', message)
        if entry[1:]:
            users.append(entry[1])
            messages.append(entry[2])
        else:
            users.append('group_notification')
            messages.append(entry[0])
    
    df['user'] = users
    df['message'] = messages
    df.drop(columns=['user_message'], inplace=True)

    # Add date-related columns
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute
    df['second'] = df['date'].dt.second

    # Calculate period (hour range)
    period = []
    for hour in df['hour']:
        if hour == 23:
            period.append(f"{hour}-{00}")
        elif hour == 0:
            period.append(f"{00}-{hour + 1}")
        else:
            period.append(f"{hour}-{hour + 1}")

    df['period'] = period

    # Return the DataFrame
    return df


# Streamlit UI
st.title("WhatsApp Chat Analyzer")

# File upload
uploaded_file = st.file_uploader("Upload your WhatsApp chat file", type=["txt"])

if uploaded_file is not None:
    data = uploaded_file.read().decode("utf-8")
    
    # Run the preprocessing function with the uploaded data
    df = preprocess(data)

    # Display the dataframe in the Streamlit app
    st.write("Processed Data:")
    st.write(df.head())
