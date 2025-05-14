import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import speech_recognition as sr
from collections import Counter
from calendar import month_name
import emoji


# Set page config
st.set_page_config(page_title="WhatsApp Chat Analyzer", layout="wide")

def listen_to_user():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Listening... Speak your question.")
        audio = recognizer.listen(source)
        try:
            query = recognizer.recognize_google(audio)
            st.success(f"🗨️ You said: {query}")
            return query.lower()
        except sr.UnknownValueError:
            st.error("Sorry, I couldn't understand. Try again.")
        except sr.RequestError:
            st.error("API unavailable or quota exceeded.")


def handle_voice_query(query, df):
    if "most active" and "weekend" in query:
        df_weekend = df[df['day_name'].isin(['Saturday', 'Sunday'])]
        top_user = df_weekend['user'].value_counts().idxmax()
        return f"The most active user on weekends is: **{top_user}**"

    elif "most used emoji" in query:
        from collections import Counter
        import emoji
        emojis = []
        for msg in df['message']:
            emojis.extend([c for c in msg if c in emoji.EMOJI_DATA])
        if emojis:
            top_emoji = Counter(emojis).most_common(1)[0][0]
            return f"The most used emoji is: {top_emoji}"
        else:
            return "No emojis found."
           
    elif ("messages by month" in query) or ("list all month" in query) or ("show all months" in query):
         df['month'] = df['date'].dt.month_name()
         df['year'] = df['date'].dt.year
     
         month_activity = df.groupby('month')['message'].count()
     
         from calendar import month_name
         month_order = list(month_name)[1:]
     
         result = ""
         for month in month_order:
             if month in month_activity:
                 result += f"{month}: {month_activity[month]} messages\n\n"
         
         return result

 
    elif "total word count" in query or "how many words" in query:
        total_words = df['message'].apply(lambda x: len(x.split())).sum()
        return f"📝 The chat contains a total of **{total_words}** words."
    
    elif "inactive" in query.lower() and "month" or "less active month" in query.lower():
        df['month_num'] = df['date'].dt.month
        df['month_name'] = df['date'].dt.month_name()
    
        # Group by month number + name to keep month order
        month_activity = df.groupby(['month_num', 'month_name'])['message'].count()
    
        least_active = month_activity.idxmin()  # (month_num, month_name)
        count = month_activity.min()
    
        return f"The least active month is {least_active[1]} with {count} messages."
    
    elif "highest activity" and "week" in query:
        activity_by_day = df.groupby('day_name').size()  # assuming 'day_name' contains days of the week
        highest_activity_day = activity_by_day.idxmax()
        return f"The day with the highest activity is: **{highest_activity_day}**"  
    
    elif "most active month" in query.lower() or "highest activity month" in query.lower():
       df['month'] = df['date'].dt.month_name()  # Extract month name
       df['year'] = df['date'].dt.year  # Extract year to handle different years
       # Group by month and count messages
       month_activity = df.groupby('month')['message'].count()
           # Get the most active month
       most_active_month = month_activity.idxmax()
       most_active_month_count = month_activity.max()
           # Show the result as a message (instead of a plot)
       return f"The most active month is {most_active_month} with {most_active_month_count} messages." 

    elif "total messages" or "how many messages" in query:
        total=df.shape[0]
        return f"💬 The chat contains a total of **{total}** messages."

    # Add more conditions as needed

    else:
       return "Sorry, I couldn't process that query yet."


# 🔧 Add background image using base64 encoding
def set_bg(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Call the function with your background image file name
set_bg("whatsapp analysis.jpg")

# Sidebar UI
st.sidebar.title("📱 WhatsApp Chat Analyzer")
uploaded_file = st.sidebar.file_uploader("Upload your WhatsApp chat file (.txt)", type="txt")

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode("utf-8")
    df = preprocessor.preprocess(data)
    st.dataframe(df)

    st.sidebar.success("✅ File uploaded successfully!")

    user_list = df['user'].unique().tolist()
    user_list.remove('group_notification')
    user_list.sort()
    user_list.insert(0, "Overall")

    selected_user = st.sidebar.selectbox("Analyze chat for", user_list)

    if st.sidebar.button("🎤 Ask by Voice"):
        query = listen_to_user()
        if query:
           response = handle_voice_query(query, df)
           st.markdown(response)
    
    if st.sidebar.button("Show Analysis using graphs"):
        num_messages, words, num_media_message, num_links = helper.fetch_stats(selected_user, df)
        st.sidebar.success("✅ Analysis complete!")

        st.markdown(f"<h2 style='color:white;'>Analysis for: <i>{selected_user}</i></h2>", unsafe_allow_html=True)
        
        st.title("📊 Top Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Messages", num_messages)
        with col2:
            st.metric("Total Words", words)
        with col3:
            st.metric("Media Messages", num_media_message)
        with col4:
            st.metric("Links Shared", num_links)

        st.title("📅 Monthly Timeline")
        timeline = helper.monthly_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(timeline['time'], timeline['message'], color='limegreen')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        st.title("🗓️ Daily Timeline")
        daily_timeline = helper.daily_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='black')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        st.title("🗺️ Activity Map")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Most Active Day")
            busy_day = helper.week_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_day.index, busy_day.values, color='orange')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        with col2:
            st.subheader("Most Active Month")
            busy_month = helper.month_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values, color='purple')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        st.title("📌 Weekly Activity Heatmap")
        user_heatmap = helper.activity_heatmap(selected_user, df)
        fig, ax = plt.subplots()
        sns.heatmap(user_heatmap, ax=ax)
        st.pyplot(fig)

        if selected_user == 'Overall':
            st.title("👥 Most Active Users")
            x, new_df = helper.most_busy_users(df)
            fig, ax = plt.subplots()
            col1, col2 = st.columns(2)

            with col1:
                ax.bar(x.index, x.values, color='red')
                st.pyplot(fig)

            with col2:
                st.dataframe(new_df)

        st.title("🌥️ Word Cloud")
        df_wc = helper.create_wordcloud(selected_user, df)
        fig, ax = plt.subplots()
        ax.imshow(df_wc)
        ax.axis("off")
        st.pyplot(fig)

        st.title("😂 Most Used Emojis")
        emoji_df = helper.emoji_helper(selected_user, df)

        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots()
            ax.bar(emoji_df[0], emoji_df[1], color='blue')
            st.pyplot(fig)
        with col2:
            st.dataframe(emoji_df)
