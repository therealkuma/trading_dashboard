import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

########################## initialize session state
# if 'authentication_status' not in st.session_state:
#     st.session_state.authentication_status = None

# if 'name' not in st.session_state:
#     st.session_state.name = None
############################################

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    if username == 'guest':
        try:
            if authenticator.register_user('Register user', preauthorization=False):
                    st.write('Please logout and log back in')
                    
        except Exception as e:
            st.error(e)
        with open('config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
        authenticator.logout('Logout', 'main', key='unique_key')
        
    else:        
        authenticator.logout('Logout', 'main', key='unique_key')
    
        st.write(f'Welcome *{name}*')
        st.title('Some content')
        st.write('haha')
        
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password  \nIf you do not have one, login as guest, passcode is 5566')
