#!/usr/bin/env python
"""

Copyright (c) 2009  Dustin Sallings <dustin@spy.net>
"""

import cStringIO as StringIO
from collections import deque

import simplejson

from twisted.python import log
from twisted.web import server, resource
from twisted.internet import task, reactor
from twisted.protocols.basic import LineOnlyReceiver

class LineHistory(deque):

    seq_id = 0

    def __init__(self, size=25):
        super(LineHistory, self).__init__([], size)

    def since(self, n):
        # If a nonsense ID comes in, scoop them all up.
        if n > self.seq_id:
            log.msg("Overriding last ID from %d to %d" % (n, self.seq_id))
            n = self.seq_id
        f = max(0, self.seq_id - n)
        rv = list(self)[0-f:] if self.seq_id >= n else []
        return rv

    def append(self, x):
        self.seq_id = self.seq_id + 1
        super(LineHistory, self).append((self.seq_id, x))

class ProcessHandler(LineOnlyReceiver):

    active = False
    delimiter = "\n"

    def __init__(self, rsrc, cmd, lineFilter):
        self.rsrc = rsrc
        self.cmd = cmd
        self.filter = lineFilter
        self.recent = LineHistory()

    def connectionMade(self):
        log.msg("Started cmd: %s" % self.cmd)
        self.active = True

    def childDataReceived(self, childFd, data):
        # XXX:  Magic for stderr handling goes here.
        lines  = (self._buffer+data).split(self.delimiter)
        self._buffer = lines.pop(-1)
        for line in lines:
            if len(line) > self.MAX_LENGTH:
                return self.lineLengthExceeded(line)
            else:
                self.lineReceived(line)
        if len(self._buffer) > self.MAX_LENGTH:
            return self.lineLengthExceeded(self._buffer)

    def lineReceived(self, line):
        filtered = self.filter(line)
        if filtered:
            self.recent.append(filtered)
            self.rsrc.lineReceived(*self.recent[-1])
            log.msg("Received line:  ``%s''" % filtered)

    def childConnectionLost(self, childFd):
        log.msg("Lost connection to %s" % childFd)

    def processEnded(self, reason):
        log.msg("Finished cmd: %s: %s" % (self.cmd, reason))
        self.active = False
        self.recent = LineHistory()

    def processExited(self, reason):
        log.msg("%s has exited: %s" % (self.cmd, reason))

class CommandResource(resource.Resource):

    max_queue_size = 100
    max_id = 1000000000

    def __init__(self, args, lineFilter=lambda l: l):
        self.requests=[]
        self.args = args
        self.known_sessions = {}
        self.process = None
        self.handler = ProcessHandler(self, args[0], lineFilter)
        l = task.LoopingCall(self.__touch_active_sessions)
        l.start(5, now=False)

    def initProcess(self):
        self.process = reactor.spawnProcess(self.handler,
                                            self.args[0], self.args)

    def lineReceived(self, line_id, line):
        for req in self.requests:
            self.__transmit_json(req, [line])

    def render_GET(self, request):
        if not self.handler.active:
            self.initProcess()
        session = request.getSession()
        if session.uid not in self.known_sessions:
            print "New session: ", session.uid
            self.known_sessions[session.uid] = True
            session.notifyOnExpire(self.__mk_session_exp_cb(session.uid))
        if not self.__deliver(request):
            self.requests.append(request)
            request.notifyFinish().addBoth(self.__req_finished, request)
        return server.NOT_DONE_YET

    def __req_finished(self, whatever, request):
        self.requests.remove(request)

    def __touch_active_sessions(self):
        for r in self.requests:
            r.getSession().touch()

    def __deliver(self, req):
        sid = req.getSession().uid
        since = int(req.args.get('n', ['0'])[0])
        data = self.handler.recent.since(since)
        log.msg("Since returned %s" % data)
        if data:
            self.__transmit_json(req, data)
            req.finish()
        return data

    def __transmit_json(self, req, data):
        j=simplejson.dumps({'max': self.handler.recent.seq_id,
                            'delivering': len(data),
                            'res': data})
        req.write(self.__mk_res(req, j, 'text/plain'))

    def __mk_session_exp_cb(self, sid):
        def f():
            print "Expired session", sid
            del self.known_sessions[sid]
            if self.handler.active and not self.known_sessions:
                self.process.signalProcess('INT')
        return f

    def __mk_res(self, req, s, t):
        req.setHeader("content-type", t)
        req.setHeader("content-length", str(len(s)))
        return s
