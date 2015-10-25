from utilities.auth_store import load_keys, update_keys, load_uid, store_uid, handle_legacy, clear_keys, clear_uid
import api.auth
from thread import start_new_thread
from config import network_reconnect_timeout, clear_server_aware_datastores
from kivy.clock import Clock
from functools import partial
from modules.core.android_utils import Toast


user_id = None

def _generate_RSA(on_done, bits=2048):
    '''
    Generate an RSA keypair with an exponent of 65537 in PEM format
    param: bits The key length in bits
    Return private key and public key
    '''
    from kivy import platform
    if platform == 'android':
        from jnius import autoclass
        KeyPairGenerator = autoclass('java.security.KeyPairGenerator')
        keyPairGen = KeyPairGenerator.getInstance("RSA")
        keyPairGen.initialize(int(bits))
        keyPair = keyPairGen.generateKeyPair()
        publicK = keyPair.getPublic()
        privateK = keyPair.getPrivate()
        Base64 = autoclass('android.util.Base64')
        pem_public_key = Base64.encodeToString(publicK.getEncoded(), Base64.DEFAULT)
        pem_private_key = Base64.encodeToString(privateK.getEncoded(), Base64.DEFAULT)
        pem_public_key = '-----BEGIN RSA PRIVATE KEY-----\n' + pem_public_key + '\n-----END RSA PRIVATE KEY-----'
        pem_private_key = '-----BEGIN RSA PRIVATE KEY-----\n' + pem_private_key + '\n-----END RSA PRIVATE KEY-----'
        from Crypto.PublicKey import RSA
        public_key = str(RSA.importKey(pem_public_key).exportKey("OpenSSH"))
        private_key = str(RSA.importKey(pem_private_key).exportKey("PEM"))
    # elif platform == 'ios':
    #     print 'generating key pair'
    #     from pyobjus import autoclass, objc_str
    else:
        print 'CRYPTO -- generating key pair'
        from Crypto.PublicKey import RSA
        new_key = RSA.generate(bits, e=65537)
        public_key = str(new_key.publickey().exportKey("OpenSSH"))
        private_key = str(new_key.exportKey("PEM"))

    #print 'WE HAVE IT ALL -- pub -- %s' % public_key
    #print 'WE HAVE IT ALL -- pri -- %s' % private_key
    #return (private_key, public_key)
    pair = (private_key, public_key)
    on_done(pair)

    # We assume we are running for a separate thread, so we need to close it nicely.
    if platform == 'android':
        from jnius import autoclass
        Thread = autoclass('java.lang.Thread')
        #print ' GETTING THREAD'
        mythread = Thread.currentThread()
        #print ' THREAD JOINING...'
        mythread.join()
        #print ' THREAD DYING...'


def _gen_RSA_and_register(on_login):
    from modules.core.android_utils import Toast
    Toast('creating new anonymous profile')

    def _continue_login(pair, dt):
        update_keys(pair)
        _do_register(pair[1], on_login=on_login)

    def _done_pair(pair):
        from kivy.clock import Clock
        from functools import partial
        Clock.schedule_once(partial(_continue_login, pair), 0.025)

    # notice we are crating the thread here, but the callback will be run from UI context
    start_new_thread(_generate_RSA, (_done_pair,))


def _on_error_reconnect(failure, reconnect_func):
    from twisted.python.failure import Failure
    if isinstance(failure, Failure):
        def reconnect(dt):
            reconnect_func()
        Toast('network error')
        Clock.schedule_once(
            reconnect,
            network_reconnect_timeout)
        return True


def _do_register(pub_key, on_login=None):
    def on_uid(new_uid):
        global user_id
        user_id = new_uid
        store_uid(new_uid)
        print('register: stored new uid %s' % new_uid)
        _login(new_uid, on_login=on_login)

    def on_error(failure, code=None):
        print 'print _do_register %s ' % str(failure)
        if not _on_error_reconnect(failure, reconnect_func=partial(_do_register, pub_key=pub_key, on_login=on_login)):
            if code == 400:
                # duplicate keys, clear them and try again
                print '_do_register force keys regeneration'
                clear_keys()
                _register(on_login=on_login)
            else:
                Toast('registration failed')

    api.auth.register(
        pub_key=pub_key,
        on_uid=on_uid,
        on_error=on_error)


def _register(on_login=None):
    global user_id
    user_id = load_uid()
    if user_id:
        return user_id
    pair = load_keys()
    if pair and all(pair):
        _do_register(pub_key=pair[1], on_login=on_login)
    else:
        clear_server_aware_datastores()
        # this function actually creates a thread and signals back when key pair is done
        _gen_RSA_and_register(on_login)


def _login(uid, on_login=None, toast=False):
    def on_token(new_token):
        print('register: received token %s' % new_token)
    def on_error(failure, code=None):
        if not _on_error_reconnect(failure, reconnect_func=partial(_login, uid=uid, on_login=on_login, toast=True)):
            # duplicate keys, clear them and try again
            print '_login force uid regeneration'
            clear_uid()
            _register(on_login=on_login)
            # Toast('login unauthorized')

    if toast:
        Toast('logging in...')

    api.auth.login(
        user_id=uid,
        on_token=(on_login or on_token),
        on_error=on_error)


def authenticate(on_login=None):
    handle_legacy()
    def resolved(base_ip):
        uid = _register(on_login)
        if uid:
            _login(uid, on_login=on_login)
    from api import resolve_base_url
    try:
        resolve_base_url(resolved)
    except Exception as e:
        from kivy.logger import Logger
        import traceback
        tb = traceback.format_exc()
        Logger.info('Authenticate ERROR: %s' % tb)


def user_authenticated():
    return load_uid() != None

user_authenticated_on_session_start = user_authenticated()

