# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011, Martín Raúl Villalba
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
##############################################################################


MAX_ACK_QUEUE = 25
MAX_MSG_QUEUE = 25

import time

from ant.core.constants import *
from ant.core.message import Message, ChannelEventMessage
from ant.core.exceptions import MessageError


def ProcessBuffer(buffer_):
    messages = []

    while True:
        hf = Message()
        try:
            msg = hf.getHandler(buffer_)
            buffer_ = buffer_[len(msg.getPayload()) + 4:]
            messages.append(msg)
        except MessageError as e:
            if e.internal == "CHECKSUM":
                buffer_ = buffer_[ord(buffer_[1]) + 4:]
            else:
                break

    return (buffer_, messages,)


def EventPump(evm):
    evm.pump_lock.acquire()
    evm.pump = True
    evm.pump_lock.release()

    go = True
    buffer_ = ''
    while go:
        evm.running_lock.acquire()
        if not evm.running:
            go = False
        evm.running_lock.release()

        buffer_ += evm.driver.read(20)
        if len(buffer_) == 0:
            continue
        buffer_, messages = ProcessBuffer(buffer_)

        for message in messages:
            for callback in evm.callbacks:
                try:
                    callback.process(message)
                except Exception as e:
                    pass


        time.sleep(0.002)

    evm.pump_lock.acquire()
    evm.pump = False
    evm.pump_lock.release()


class EventCallback(object):
    def process(self, msg):
        pass


class AckCallback(EventCallback):
    def __init__(self, evm):
        self.evm = evm

    def process(self, msg):
        if isinstance(msg, ChannelEventMessage):
            self.evm.ack_lock.acquire()
            self.evm.ack.append(msg)
            if len(self.evm.ack) > MAX_ACK_QUEUE:
                self.evm.ack = self.evm.ack[-MAX_ACK_QUEUE:]
            self.evm.ack_lock.release()


class MsgCallback(EventCallback):
    def __init__(self, evm):
        self.evm = evm

    def process(self, msg):
        self.evm.msg_lock.acquire()
        self.evm.msg.append(msg)
        if len(self.evm.msg) > MAX_MSG_QUEUE:
            self.evm.msg = self.evm.msg[-MAX_MSG_QUEUE:]
        self.evm.msg_lock.release()


class EventMachine(object):
   

    def __init__(self, driver):
        self.driver = driver
        self.callbacks = []
        self.running = False
        self.pump = False
        self.ack = []
        self.msg = []
        self.registerCallback(AckCallback(self))
        self.registerCallback(MsgCallback(self))

    def registerCallback(self, callback):
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def removeCallback(self, callback):
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def waitForAck(self, msg):
        while True:
            for emsg in self.ack:
                if msg.getType() != emsg.getMessageID():
                    continue
                self.ack.remove(emsg)
                self.ack_lock.release()
                return emsg.getMessageCode()
            time.sleep(0.002)

    def waitForMessage(self, class_):
        while True:
            self.msg_lock.acquire()
            for emsg in self.msg:
                if not isinstance(emsg, class_):
                    continue
                self.msg.remove(emsg)
                self.msg_lock.release()
                return emsg
            self.msg_lock.release()
            time.sleep(0.002)

    def start(self, driver=None):
        

        if self.running:
            
            return
        self.running = True
        if driver is not None:
            self.driver = driver

        while True:
            
            if self.pump:
                
                break
            
            time.sleep(0.001)

        

    def stop(self):
        

        if not self.running:
            
            return
        self.running = False
        

        while True:
            
            if not self.pump:
                
                break
            
            time.sleep(0.001)
