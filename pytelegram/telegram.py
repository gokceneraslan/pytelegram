from . import ffi, tgl

from .callbacks import *

import os
import tempfile
import sys
import signal

@ffi.callback('void (*signal_cb) (int fd, short event, void *arg)')
def signal_cb(fd, event, arg):
    os._exit(0)

class Telegram(object):
    def __init__(self,
                 rsa_key,
                 update_callbacks,
                 app_id = 2899,
                 app_hash = "36722c72256a24c1225de00eb6a1ca74",
                 download_dir = None,
                 config_dir = os.path.expanduser('~/.telegram-cli')):

        self._state = ffi.new('struct tgl_state *')
        self._download_dir = download_dir
        self._config_dir = config_dir

        #dirs and files
        if not os.path.exists(self._config_dir):
            os.makedirs(self._config_dir)

        self._auth_file = os.path.join(self._config_dir, 'auth')
        self._state_file = os.path.join(self._config_dir, 'state')
        self._secret_chat_file = os.path.join(self._config_dir, 'secret')

        self._app_id = app_id
        self._app_hash = app_hash
        self._rsa_keypath = rsa_key

        self.set_callback(update_callbacks)
        tgl.tgln_set_evbase(self._state)

        self.set_net_methods(ffi.addressof(tgl.tgl_conn_methods))
        self.set_timer_methods(ffi.addressof(tgl.tgl_libevent_timers))
        self.set_serialize_methods(ffi.addressof(tgl.tgl_file_methods))

        self.set_rsa_key(self._rsa_keypath)

        if self._download_dir is None:
            self._download_dir = tempfile.mkdtemp(prefix = 'telegram')

        self.set_download_directory(self._download_dir)

        self.register_app_id(self._app_id, self._app_hash)

        tgl.tgl_init(self._state)

        self.set_auth_file(self._auth_file)
        self.set_state_file(self._state_file)
        self.set_secret_chat_file(self._secret_chat_file)

        self.load_auth()
        self.load_state()
        self.load_secret_chats()

        tgl.tgln_set_signal_handler(self._state, signal.SIGINT, signal_cb)


    def set_callback(self, cb):
        tgl.tgl_set_callback(self._state, cb)

    def set_net_methods(self, m):
        self._state.net_methods = m

    def set_timer_methods(self, m):
        self._state.timer_methods = m

    def set_serialize_methods(self, m):
        self._state.serialize_methods = m

    def set_download_directory(self, dd):
        self._download_dir = dd
        tgl.tgl_set_download_directory(self._state,
                self._download_dir.encode())

    def set_auth_file(self, path):
        self._auth_file = path
        tgl.tgl_set_auth_file_path(self._state, self._auth_file.encode())

    def set_secret_chat_file(self, path):
        self._secret_chat_file = path
        tgl.tgl_set_secret_chat_file_path(self._state,
                self._secret_chat_file.encode())

    def set_state_file(self, path):
        self._state_file = path
        tgl.tgl_set_state_file_path(self._state, self._state_file.encode())

    def set_rsa_key(self, keypath):
        self._rsa_keypath = keypath
        tgl.tgl_set_rsa_key(self._state, self._rsa_keypath.encode())

    def register_app_id(self, id_, hash_):
        self._appid = id_
        self._apphash = hash_

        tgl.tgl_register_app_id(self._state, self._appid,
                self._apphash.encode())

    def load_auth(self):
        self._state.serialize_methods.load_auth(self._state)

    def store_auth(self):
        self._state.serialize_methods.store_auth(self._state)

    def load_state(self):
        self._state.serialize_methods.load_state(self._state)

    def store_state(self):
        self._state.serialize_methods.store_state(self._state)

    def load_secret_chats(self):
        self._state.serialize_methods.load_secret_chats(self._state)

    def store_secret_chats(self):
        self._state.serialize_methods.store_secret_chats(self._state)

    def loop(self, flags = 0, is_end = None):
        if is_end is None:
            cb = ffi.NULL
        else:
            cb = ffi.callback("int (*)(void)", is_end)

        tgl.wait_for_event(self._state, flags, cb)

    def all_authorized(self):
        s = self._state
        max_dc = s.max_dc_num
        return all([tgl.tgl_authorized_dc(s, s.DC_list[i])
                   for i in range(1, max_dc+1)]) #WTF!!!

    def check_authorization(self):

        for i in range(1, self._state.max_dc_num+1):
            if self._state.DC_list[i] and not tgl.tgl_authorized_dc(self._state, self._state.DC_list[i]):
                raise Exception("DC[%d] is not authorized." % (i-1))
        return True

    def wait_until_authorization(self):
        self.loop(0, lambda: int(self.all_authorized()))


    def reset_authorization(self):
        tgl.bl_do_reset_authorization(self._state)

    def signed_in(self):
        return tgl.tgl_signed_dc (self._state, self._state.DC_working)

    def sign_in(self):
        if not self.signed_in():
            username = input("Telephone number (with '+' sign): ").encode()

            registered = False
            hash_ = None

            @ffi.callback("void (*)(struct tgl_state *, void *, int , int , const char *)")
            def sign_in_cb(tls, extra, success, registeredarg, mhasharg):

                nonlocal registered
                nonlocal hash_

                if success:
                    registered = registeredarg
                    hash_ = mhasharg

            tgl.tgl_do_send_code (self._state, username, sign_in_cb, ffi.NULL);
            self.loop(0, lambda: hash_ is not None)

            if registered:
                print('Code from SMS (if you did not receive an SMS and want' \
                      ' to be called, type "call"): ', end=' ')

                while True:
                    code = input()
                    if code.strip() == 'call':
                        tgl.tgl_do_phone_call (self._state, username, hash_, ffi.NULL, ffi.NULL);
                        print("Code: ", end=' ')
                        continue

                    signed_in = False
                    @ffi.callback('void (*)(struct tgl_state *TLSR, void *extra, int' \
                                  ' success, struct tgl_user *U)')
                    def sign_in_result_cb(tls, extra, success, user):
                        nonlocal signed_in
                        if success:
                            signed_in = True

                    if tgl.tgl_do_send_code_result(self._state, username,
                            hash_, code.encode(), sign_in_result_cb, ffi.NULL) >= 0:
                        break
                    print("Invalid code. Try again: ", end=' ')

            else:
                print("Registration is not implemented yet...")
                sys.exit(0)

            self.loop(0, lambda: int(signed_in))

    def check_sign_in(self):

        @ffi.callback("void (*)(struct tgl_state *TLSR, void *DC, int success)")
        def cb(tls, dc, success):
            assert success

        for i in range(1, self._state.max_dc_num+1):
            if self._state.DC_list[i] and not tgl.tgl_signed_dc(self._state, self._state.DC_list[i]):
                tgl.tgl_do_export_auth(self._state, i, cb, self._state.DC_list[i])
                self.loop(0, lambda: tgl.tgl_signed_dc(self._state, self._state.DC_list[i]))
                assert tgl.tgl_signed_dc(self._state, self._state.DC_list[i])

    def send_all_unsent(self):
        tgl.tglm_send_all_unsent(self._state)

    def get_difference(self, sync_from_start = 0):
        diff_success = 0

        @ffi.callback("void (*)(struct tgl_state *, void *, int)")
        def get_diff_cb(tls, extra, success):
            nonlocal diff_success
            assert success
            diff_success = 1


        tgl.tgl_do_get_difference(self._state, sync_from_start, get_diff_cb, ffi.NULL)

        self.loop(0, lambda: diff_success)
        assert not (self._state.locks & tgl.TGL_LOCK_DIFF)

        self._state.started = 1

