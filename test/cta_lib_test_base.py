import unittest
import logging
import os
from typing import Dict, List
import evtset.eventSet
from cta_lib import CtaLib

# complex type definition
Sequence = Dict[str, List[int]]

class CtaTestBase(unittest.TestCase):

    # static variables ----------------
    CTA_DEVICE_NAME = ""
    EVT_SET_CHAN_NAME = ""

    # setup/tearDown functions --------
    def setUp(self):
        """
        This function is a test fixture.
        """
        ## setup logging
        log_level = "WARNING"
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError("Invalid log_level:{}".format(log_level))
        logging.basicConfig(level=numeric_level,
                            format='%(asctime)s | %(levelname)8s | %(message)s')
        logging.warning("CtaTestBase.setUp() is running")

        ## check arguments from environment variables
        if CtaTestBase.CTA_DEVICE_NAME == "":
            raise RuntimeError("CTA deice name is not defined")
        if CtaTestBase.EVT_SET_CHAN_NAME == "":
            raise RuntimeError("Event set channel name is not defined")
        logging.warning("CTA_DEVICE_NAME={}".format(CtaTestBase.CTA_DEVICE_NAME))
        logging.warning("EVT_SET_CHAN_NAME={}".format(CtaTestBase.EVT_SET_CHAN_NAME))

        # create cta lib
        self.clo = CtaLib(CtaTestBase.CTA_DEVICE_NAME) # clo = CTA lib object

        # assert cta is not running
        self.assertFalse(self.clo.is_running())

        # set default config on cta
        self.setDefaultConfig()

    def tearDown(self):
        """
        This function is a test fixture.
        """
        logging.warning("CtaTestBase.tearDown() is running")
        self.clo.disconnect_pvs()

    # assert functions ----------------
    def assertSeqInDataBuffer(self, seq_up: Sequence = None, pid_start: int = None):
        """
        This function is a unit test asserter.
        It takes two arguments: <seq_up>, <pid_start>
        The function retrives event set data from the data buffer and asserts
        that the data contains the sequence <seq_up> at <pid_start>.
        
        If <seq_up> is not given, the default sequence as setup by
        CtaTestBase.setDefaultConfig() is expected.

        If <pid_start> is not given, it is read from the CTA "started at" record.
        """

        # setup default values of arguments
        if seq_up is None:
            seq_up = self.default_sequence

        if pid_start is None:
            pid_start = self.clo.get_started_at()
        
        # prepare arguments for data buffer retrieval
        length = len(list(seq_up.values())[0])
        event_codes = list(range(200, 220))
        pulseids = list(range(pid_start, pid_start + length))

        # fetch data from data buffer
        logging.warning("fetching data from data buffer: pulseids={}-{}".format(pulseids[0],pulseids[-1]))
        it = evtset.eventSet.fetch_data_pid(CtaTestBase.EVT_SET_CHAN_NAME, event_codes, pulseids)

        # initialize seq_db = sequence in data buffer
        # refer to (1) for format
        seq_db = {}
        for i in range(200, 220):
            seq_db[i] = [0] * length
        idx = 0

        # translate from data buffer format to sequence format
        # refer to (2) for data format
        for data in it:

            pulseids = list(data.keys())
            pulseids.sort()

            # debugging
            #print("data={}".format(data))
            #print("pulseids={}".format(pulseids))
            #print("len(pulseids)={}".format(len(pulseids)))

            for pid in pulseids:
                for i in range(20):
                    try:
                        seq_db[200 + i][idx] = int(data[pid][1][i])
                    except TypeError as error:
                        logging.error("Data from data buffer contains missing pulse: data[{}]={}".format(pid, data[pid]))
                        break
                idx += 1

        # assert that uploaded and retrieved sequence match
        self.assertEqual(seq_up, seq_db)

    # helper functions ----------------
    def computeNTimesSequence(self, n: int, seq: Sequence = None) -> Sequence:
        """
        This function is a helper function.
        It takes two arguments: <n> and <seq>
        It multiplies the sequence <seq> <n> times and returnes the new sequence.

        If <seq_up> is not given, the default sequence as setup by
        CtaTestBase.setDefaultConfig() is used.
        """

        if seq is None:
            seq = self.default_sequence

        seq_n = {}

        for key in seq:
            seq_n[key] = seq[key] * n

        return seq_n

    def setDefaultConfig(self):
        """
        This function is a helper function.
        It creates a sequence and uploads it to the CTA.
        Furthermore it sets a default repetition and start configuration.
        """

        logging.warning("CtaTestBase.setDefaultConfig() is running")

        # create default sequence (walking ones)
        sequence = {}
        sequence[200] = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sequence[201] = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sequence[202] = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sequence[203] = [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sequence[204] = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sequence[205] = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sequence[206] = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sequence[207] = [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sequence[208] = [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sequence[209] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sequence[210] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sequence[211] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        sequence[212] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        sequence[213] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
        sequence[214] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
        sequence[215] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        sequence[216] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
        sequence[217] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
        sequence[218] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
        sequence[219] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        self.default_sequence = sequence

        # upload
        self.clo.upload(self.default_sequence)

        # set repetition configuration
        self.clo.set_repetition_config(config={'mode': CtaLib.RepetitionMode.NTIMES, 'n': 1})

        # set start config
        self.clo.set_start_config(config={'mode': CtaLib.StartMode.MODULO, 'divisor': 10, 'offset': 0})

# read in environment variables to parametrise the test
CtaTestBase.CTA_DEVICE_NAME = os.environ.get('CTA_DEVICE_NAME', CtaTestBase.CTA_DEVICE_NAME)
CtaTestBase.EVT_SET_CHAN_NAME = os.environ.get('EVT_SET_CHAN_NAME', CtaTestBase.EVT_SET_CHAN_NAME)

# (1) sequence format
# seq_db = {
#            <event code>:
#            [<bool pid x>, <bool pid x+1>, ...],
#            <event code>:
#            ...
#          }
# (2) data buffer data format
# data = {
#          <pulse id x>:
#          (
#                       <time stamp>,
#                       [<bool event code 200>, <bool event code 201, ...}
#          ),
#          <pulse id y>:
#         ...
#        }

