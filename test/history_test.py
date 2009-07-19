from twisted.trial import unittest
from twisted.internet import defer

from tdf import cmds

class LineHistoryTest(unittest.TestCase):

    lh = None

    def setUp(self):
        self.lh = cmds.LineHistory()

    def testEmpty(self):
        self.assertFalse(self.lh)
        stuff = self.lh.since(9324)

        self.assertFalse(stuff)

    def testOne(self):
        self.lh.append("hi")
        self.assertTrue(self.lh)

        stuff = self.lh.since(8248)
        self.assertEquals(1, len(stuff))

        self.assertEquals(stuff[0], (1, "hi"))

    def testFive(self):
        for w in "this here is a test".split():
            self.lh.append(w)

        stuff = self.lh.since(8294)
        self.assertEquals(5, len(stuff))
        self.assertEquals(stuff[0], (1, 'this'))
        self.assertEquals(stuff[-1], (5, 'test'))

        stuff = self.lh.since(3)
        self.assertEquals(2, len(stuff))

        self.assertEquals(stuff[0], (4, 'a'))
        self.assertEquals(stuff[-1], (5, 'test'))
