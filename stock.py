# !pip install streamlit
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf 
from ta.volatility import BollingerBands
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

# for more about ta liabrary --> https://github.com/bukosabino/ta
#https://technical-analysis-library-in-python.readthedocs.io/en/latest/
######################
#login for users #    
#####################
def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"]
            == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store username + password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
    st.write("Here goes your normal Streamlit app...")
    st.button("Click me")

    #defining ticker variables
    #Bitcoin = 'BTC-USD'
    #Ethereum = 'ETH-USD'
    #Ripple = 'XRP-USD'
    #BitcoinCash = 'BCH-USD'

    ##################
    # Set up sidebar #
    ##################

    # Add in location to select image.

    option = st.sidebar.selectbox('Select one symbol', ( 'BTC-USD', 'ETH-USD','XRP-USD','BCH-USD'))


    import datetime

    today = datetime.date.today()
    before = today - datetime.timedelta(days=700)
    start_date = st.sidebar.date_input('Start date', before)
    end_date = st.sidebar.date_input('End date', today)
    if start_date < end_date:
        st.sidebar.success('Start date: `%s`\n\nEnd date:`%s`' % (start_date, end_date))
    else:
        st.sidebar.error('Error: End date must fall after start date.')


    ##############
    # Stock data #
    ##############

    # https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#momentum-indicators

    df = yf.download(option,start= start_date,end= end_date, progress=False)

    indicator_bb = BollingerBands(df['Close'])

    bb = df
    bb['bb_h'] = indicator_bb.bollinger_hband()
    bb['bb_l'] = indicator_bb.bollinger_lband()
    bb = bb[['Close','bb_h','bb_l']]

    macd = MACD(df['Close']).macd()

    rsi = RSIIndicator(df['Close']).rsi()

    ema = EMAIndicator(df['Close'],window=20).ema_indicator().fillna(0)


    ###################
    # Set up main app #
    ###################

    st.write('Stock Bollinger Bands')

    st.line_chart(bb)

    progress_bar = st.progress(0)

    # https://share.streamlit.io/daniellewisdl/streamlit-cheat-sheet/app.py

    st.write('Stock Moving Average Convergence Divergence (MACD)')
    st.area_chart(macd)

    st.write('Stock RSI ')
    st.line_chart(rsi)

    st.write('Stock EMA 20 ')
    st.line_chart(ema)

    st.write('Recent data ')
    st.dataframe(df.tail(10))










