from kivy.utils import platform
from kivy.core.window import Keyboard
from utilities.datastore import get_datastore

base_url = 'https://insiderr-alpha.appspot.com/api/v1'

invite_url = 'http://insiderr.com/invite'
rate_url = 'https://play.google.com/insiderr'

app_version = 'unknown'
app_platform = platform
def set_app_version(version):
    global app_version
    app_version = str(version)

if platform == 'android':

    keys = {
        'back': Keyboard.keycodes['escape'],
        'load': 319 # menu button
    }

else:

    keys = {
        'back': Keyboard.keycodes['f2'],
        'load': Keyboard.keycodes['f4']
    }


share_actions = [
    {'title': 'Linkedin', 'key': 'linkedin'},
    {'title': 'Facebook', 'key': 'facebook'},
    {'title': 'Twitter', 'key': 'twitter'},
    {'title': 'Message', 'key': 'message'},
    {'title': 'Whatsapp', 'key': 'whatsapp'},
    {'title': 'More', 'key': 'more-options'},
]

post_themes = 'data/post_themes/themes.json'

post_roles = [
    {'key': 'anonymous', 'title': '#anonymous', 'prefix': 'Posting as '},
   # {'key': 'industry', 'title': '#industry', 'prefix': 'Posting under '},
    #{'key': 'company', 'title': '#company', 'prefix': 'Posting under '},
    #{'key': 'position', 'title': '#position', 'prefix': 'Posting as a{vowel} '},
#    {'key': 'expertise', 'title': '#expertise', 'prefix': 'Posting as a{vowel} ', 'suffix': ' expert'},
]

sys_posts_content = [
    {'when': 'once', 'background': '1.jpg', 'action': 'close', 'content': ' '}, # 'Co Founders - Are you aiming for an exit or an IPO?'},
    {'when': 'linkedin', 'button': 'Login with linkedin', 'background': 'bkg.jpg', 'action': 'linkedin', 'content': 'Stay anonymous! but get your personalized business feed by\nlogging in with linkedin.'},
    {'when': 'every', 'button': 'send invitation', 'background': 'bkg.jpg', 'action': 'invite', 'content': 'Invite your friends'},
]

temp_images_path = 'data/post_themes/images-temp/'

feed_placeholder = 'data/placeholder.png'

tutorial_path = 'data/tutorial/'

system_posts_path = 'data/system/'

post_length_limit = 147
comment_length_limit = 400

# post clickable area (to generate the 'item_clicked' event)
post_click_area = (.85, .7)

# Datastores

auth_ds = get_datastore(key='auth', datatype=dict, persistent=True)
attitude_ds = get_datastore(key='attitude', datatype=dict, persistent=True)
commented_ds = get_datastore(key='commented', datatype=set, persistent=True)
favorites_ds = get_datastore(key='favorites', datatype=set, persistent=True)
favs_data_ds = get_datastore(key='favs_data', datatype=dict, persistent=True)
linkedin_ds = get_datastore(key='linkedin', datatype=dict, persistent=True)
removed_ds = get_datastore(key='removed', datatype=set, persistent=True)
google_analytics_ds = get_datastore(key='google_analytics', datatype=dict, persistent=True)

def clear_server_aware_datastores():
    ''' Called when new user credentials are composed for a new server
    '''
    attitude_ds.clear()
    commented_ds.clear()
    favorites_ds.clear()
    favs_data_ds.clear()
    removed_ds.clear()


# Network
network_reconnect_timeout = 10
