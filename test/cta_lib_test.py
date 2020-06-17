from cta_lib_test_base import CtaTestBase
from cta_lib import CtaLib
import logging
import time

class StartConfigTests(CtaTestBase):

    def test_start_immediatly(self):

        logging.warning("StartConfigTests.test_start_immediatly() is running")

        # set start config
        self.clo.set_start_config(config={'mode': CtaLib.StartMode.IMMEDIATE})

        # start and wait some time
        self.clo.start()
        time.sleep(5)
        self.assertFalse(self.clo.is_running())

        # assert sequence in data buffer
        self.assertSeqInDataBuffer()

    def test_start_modulo(self):

        logging.warning("StartConfigTests.test_start_modulo() is running")

        # test vector definition (divisor, offset)
        test_vector = [(2, 0), (4, 0), (10, 0), (100, 0), (4, 1), (100, 50)]

        # interate over test vector
        for divisor, offset in test_vector:

            # set start config
            self.clo.set_start_config(config={'mode': CtaLib.StartMode.MODULO, 'divisor': divisor, 'offset': offset})

            # start and wait some time
            self.clo.start()
            time.sleep(5)
            self.assertFalse(self.clo.is_running())

            # assert started config
            pid_start = self.clo.get_started_at()
            self.assertTrue(((pid_start % divisor) - offset) == 0)

            # assert sequence in data buffer
            self.assertSeqInDataBuffer(pid_start=pid_start)

class RepetitionConfigTests(CtaTestBase):

    def test_number_of_repetitions(self):

        # define test vector
        test_vector = [1, 2, 10]

        # for each item in test vector
        #   set repetition config, start, wait some time
        #   assert not running, assert sequence in data buffer
        for n in test_vector:
            self.clo.set_repetition_config(config={'mode': CtaLib.RepetitionMode.NTIMES, 'n': n})
            self.clo.start()
            time.sleep(5)
            self.assertFalse(self.clo.is_running())
            self.assertSeqInDataBuffer(seq_up=self.computeNTimesSequence(n))

    def test_forever(self):

        logging.warning("RepetitionConfigTests.test_forever() is running")

        # set repetition config
        self.clo.set_repetition_config(config={'mode': CtaLib.RepetitionMode.FOREVER})

        # start, wait some time, assert running, stop, assert not running
        self.clo.start()
        time.sleep(5)
        self.assertTrue(self.clo.is_running())
        self.clo.stop()
        time.sleep(1)
        self.assertFalse(self.clo.is_running())

        # assert repetition 0 of sequence in data buffer
        self.assertSeqInDataBuffer()

