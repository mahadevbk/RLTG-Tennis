import streamlit as st
import pandas as pd

# Define available players
available_players = ['Player 1', 'Player 2', 'Player 3', 'Player 4', 'Player 5', 'Player 6']

# Placeholder for stats and rankings (assuming a sample structure)
stats = {
    'Player 1': {'Points': 10, 'Wins': 5, 'Games Won': 20},
    'Player 2': {'Points': 12, 'Wins': 6, 'Games Won': 22},
    'Player 3': {'Points': 15, 'Wins': 7, 'Games Won': 25},
    'Player 4': {'Points': 8, 'Wins': 4, 'Games Won': 18},
    'Player 5': {'Points': 20, 'Wins': 10, 'Games Won': 30},
    'Player 6': {'Points': 18, 'Wins': 9, 'Games Won': 28},
}

# Create a DataFrame for rankings
rankings = pd.DataFrame.from_dict(stats, orient='index')

# Streamlit App UI
st.title("Tennis Match Setup")

# Match type selection
match_type = st.selectbox("Select Match Type", ["Singles", "Doubles"])

if match_type == "Singles":
    # Player 1 selection
    p1 = st.selectbox("Player 1", available_players)
    
    # Filter available players to exclude selected player (p1)
    available_players = [player for player in available_players if player != p1]
    
    # Player 2 selection
    p2 = st.selectbox("Player 2", available_players)
    
    # Create teams
    team1 = [p1]
    team2 = [p2]

elif match_type == "Doubles":
    # Team 1 Player 1 selection
    p1 = st.selectbox("Team 1 - Player 1", available_players, key="t1p1")
    
    # Filter available players to exclude selected player (p1)
    available_players = [player for player in available_players if player != p1]
    
    # Team 1 Player 2 selection
    p2 = st.selectbox("Team 1 - Player 2", available_players, key="t1p2")
    
    # Filter available players to exclude selected player (p2)
    available_players = [player for player in available_players if player != p2]
    
    # Team 2 Player 1 selection
    p3 = st.selectbox("Team 2 - Player 1", available_players, key="t2p1")
    
    # Filter available players to exclude selected player (p3)
    available_players = [player for player in available_players if player != p3]
    
    # Team 2 Player 2 selection
    p4 = st.selectbox("Team 2 - Player 2", available_players, key="t2p2")
    
    # Create teams
    team1 = [p1, p2]
    team2 = [p3, p4]

# Display selected teams
st.write("Team 1:", team1)
st.write("Team 2:", team2)

# Display rankings based on the columns "Points", "Wins", "Games Won"
rankings_sorted = rankings.sort_values(by=["Points", "Wins", "Games Won"], ascending=False)

# Display the sorted rankings
st.header("Player Rankings")
st.dataframe(rankings_sorted.reset_index(drop=True))

# Player insights
st.header("Individual Player Insights")
for player, data in stats.items():
    st.subheader(f"{player}'s Stats")
    st.write(data)
