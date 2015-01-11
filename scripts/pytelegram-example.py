#!/usr/bin/env python3

import sys

from pytelegram.telegram import Telegram
from pytelegram import ffi, tgl
from pytelegram.callbacks import generate_tgl_update


@ffi.callback("void(struct tgl_state *, struct tgl_message *)")
def _msg_cb(tls, msg):
    assert msg
    if msg.flags & (tgl.FLAG_MESSAGE_EMPTY | tgl.FLAG_DELETED):
        return
    if not (msg.flags & tgl.FLAG_CREATED):
        return
    if msg.service:
        pass #TODO: implement
        return

    if not msg.to_id.type:
        return

    if msg.message and len(ffi.string(msg.message)):
        print("New message: ", ffi.string(msg.message).decode())


if len(sys.argv) != 2:
    print("Usage: %s telegram_rsa_key_path" % sys.argv[0])
    sys.exit()


upd_cb = generate_tgl_update()
upd_cb.new_msg = _msg_cb
upd_cb.msg_receive = _msg_cb


tg = Telegram(rsa_key = sys.argv[1],
              update_callbacks = upd_cb)

#tg._state.verbosity = 6

#tg.reset_authorization()
tg.wait_until_authorization()
tg.check_authorization()
print("All DCs are authorized.")

tg.sign_in()
tg.check_sign_in()
print("Signed in.")

tg.store_auth()

tg.send_all_unsent()
print("All unsent msgs are sent.")

tg.get_difference()
print("Entering main loop...")
tg.loop()
