"""
The complex triggering application (CTA) is an application which allows the
user to inject a user defined sequence of events in a subtree of the timing
tree.
The CTA runs on an IOC. There are two ways to program and control it.
The first is via the GUI and the second is this python library.
"""
import logging
import time
import threading
from enum import IntEnum
import numpy
from epics import PV

# pylint: disable=R0902

class CtaLib:
    """
    Create an object of this class to control one sequence of a CTA.
    """

    def __init__(self, device, sequence=0, log_level="warning"):
        """
        Constructor

        Arguments
        device: device name (e.g. SAR-CCTA-ESA)
        sequence: sequence number (default = 0)
        log_level: critical, error, warning, info, debug
        """
        self._constants = dict()
        self._constants['event_code_range_base'] = 200
        self._constants['num_of_event_codes'] = 20
        self._constants['num_of_pvs'] = 30

        # setup logging
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log_level: %s' % log_level)
        logging.basicConfig(level=numeric_level,
                            format='%(asctime)s | %(levelname)8s | %(message)s')
        logging.info('__init__() is running (device=%s', device)

        # create threading event
        self._event = threading.Event()

        # create connection housekeeper
        self._num_connected = 0

        # create attributes for callback support
        self._run_status_callbacks = list()
        self._rep_config_callbacks = list()
        self._start_config_callbacks = list()
        self._sequence_callbacks = list()

        # create pv objects
        self._pvs = dict()

        pv_name = device + ':SerMaxLen-O'
        self._pvs['SerMaxLen-O'] = PV(
            pv_name,
            connection_callback=self._connection_callback)

        pv_name = device + ':seq' + str(sequence) + 'Ctrl-Length-I'
        self._pvs['Ctrl-Length-I'] = PV(
            pv_name,
            connection_callback=self._connection_callback)
        pv_name = device + ':seq' + str(sequence) + 'Ctrl-Cycles-I'
        self._pvs['Ctrl-Cycles-I'] = PV(
            pv_name,
            callback=self._rep_config_callback,
            connection_callback=self._connection_callback)
        pv_name = device + ':seq' + str(sequence) + 'Ctrl-SCfgMode-I'
        self._pvs['Ctrl-SCfgMode-I'] = PV(
            pv_name,
            callback=self._start_config_callback,
            connection_callback=self._connection_callback)
        pv_name = device + ':seq' + str(sequence) + 'Ctrl-SCfgModDivisor-I'
        self._pvs['Ctrl-SCfgModDivisor-I'] = PV(
            pv_name,
            callback=self._start_config_callback,
            connection_callback=self._connection_callback)
        pv_name = device + ':seq' + str(sequence) + 'Ctrl-SCfgModOffset-I'
        self._pvs['Ctrl-SCfgModOffset-I'] = PV(
            pv_name,
            callback=self._start_config_callback,
            connection_callback=self._connection_callback)
        pv_name = device + ':seq' + str(sequence) + 'Ctrl-Start-I'
        self._pvs['Ctrl-Start-I'] = PV(
            pv_name,
            connection_callback=self._connection_callback)
        pv_name = device + ':seq' + str(sequence) + 'Ctrl-Stop-I'
        self._pvs['Ctrl-Stop-I'] = PV(
            pv_name,
            connection_callback=self._connection_callback)
        pv_name = device + ':seq' + str(sequence) + 'Ctrl-IsRunning-O'
        self._pvs['Ctrl-IsRunning-O'] = PV(
            pv_name,
            callback=self._run_status_callabck,
            connection_callback=self._connection_callback)

        pv_name = device + ':seq' + str(sequence) + 'Ctrl-StartedAt-O'
        self._pvs['Ctrl-StartedAt-O'] = PV(
            pv_name,
            callback=self._run_status_callabck,
            connection_callback=self._connection_callback)

        self._pvs['Data-I'] = list()
        for i in range(0, self._constants['num_of_event_codes']):
            pv_name = device + ':seq' + str(sequence) + 'Ser' + str(i) + '-Data-I'
            self._pvs['Data-I'].append(PV(
                pv_name,
                callback=self._sequence_callback,
                connection_callback=self._connection_callback))

        # wait for the connections to be established
        if not self._event.wait(timeout=5.0):
            raise RuntimeError('Some PV(s) is/are not connected')
        time.sleep(1) # NOTE01

        # logging
        for i in range(0, self._constants['num_of_event_codes']):
            logging.debug('NORD of %d: %s', i, str(self._pvs['Data-I'][i]))
        logging.info('__init__() is done')

    def __del__(self):
        """
        Deconstructor
        """

        logging.info('__del__() is running')

        logging.info('__del__() is done')

    def disconnect_pvs(self):
        """
        Disconnect all pvs

        Actually this should be done in the destructor.
        If we do we get the following error message:
          FATAL: exception not rethrown
          CA client library tcp receive thread terminating due to a
          non-standard C++ exception
        Reason unknown.
        """
        logging.info('disconnect_pvs is running')

        # disconnect connections and clear all callbacks
        for key, pv in self._pvs.items(): # pylint: disable=C0103
            if key == 'Data-I':
                for i in range(0, self._constants['num_of_event_codes']):
                    pv[i].disconnect()
            else:
                pv.disconnect()

        logging.info('disconnect_pvs is done')

    def get_max_length(self):
        """
        Get the maximal length of a sequence

        Return
        max_length: maximal length of a sequence
        """
        logging.info('get_max_length() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # get max length
        max_length = self._pvs['SerMaxLen-O'].get()

        logging.info('get_max_length() is done')

        return max_length

    def get_length(self):
        """
        Get the length of the sequence on the IOC

        Return
        length: length of the sequence
        """
        logging.info('get_length() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # get length
        length = self._pvs['Ctrl-Length-I'].get()

        logging.info('get_length() is done')

        return length

    def upload(self, seq):
        """
        Upload a sequence to the IOC

        Arguments
        seq: The sequence to be uploaded to the IOC.
             A sequence is a dictionary where each key value pair represents a series.
             A series is a list of 0's and 1's which defines, if the corresponding event code
             is sent in the corresponding machine pulse.
             The key is an integer and represents the event code.
             The value is the series.
             If a certain event code is not sent in the sequence, it may or may not
             not be present in the dictionary.
             Example:
                 seq = {200: [1, 0], 201: [1, 1]}
                 =>
                 machine pulse     x: event code 200 is sent
                 machine pulse x + 1: event code 200 and 201 are sent
        """

        logging.info('upload() is running')

        # check the sequence
        self.check_sequence(seq)

        # fill empty series
        seq = self.fill_empty_series(seq)

        # logging
        logging.debug('upload() upload: %s', str(seq))

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # upload seq to pvs
        for i in range(0, self._constants['num_of_event_codes']):
            self._pvs['Data-I'][i].put(
                numpy.array(seq[self._constants['event_code_range_base'] + i]), wait=True)

        # set length
        self._pvs['Ctrl-Length-I'].put(len(seq[self._constants['event_code_range_base']]),
                                       wait=True)

        logging.info('upload() is done')

    def download(self):
        """
        Download a sequence from the IOC

        Return
        seq: The sequence downloaded from the IOC.
             Refer to the upload method for a definition of seq.
        """

        logging.info('download() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # download
        seq = {}
        for i in range(0, self._constants['num_of_event_codes']):
            logging.debug('NORD of %d: %s', i, str(self._pvs['Data-I'][i]))
            seq[self._constants['event_code_range_base'] + i] = numpy.atleast_1d(
                self._pvs['Data-I'][i].get()).tolist()

        # logging
        logging.debug('download() downloaded: %s', str(seq))

        # check the sequence
        self.check_sequence(seq)

        logging.info('download() is done')

        return seq

    class RepetitionMode(IntEnum):
        """
        Enumeration of repetition modes
        """
        FOREVER = 0
        NTIMES = 1

    def set_repetition_config(self, *, config):
        """
        Set the repetition configuration.

        The repetition configuration defines how many times the sequence is
        repeated by the CTA.
        The repetition configuration is defined with a dictionary.
        The key 'mode' is mandatory and can have the following values:
        * CtaLib.RepetitionMode.FOREVER
          The sequence is repeated forever. It must be stopped by calling
          CtaLib.stop()
        * CtaLib.RepetitionMode.NTIMES
          The sequence is repeated n times, where n must be provided as value of
          the key 'n'.

        Arguments:
        config: dictionary describing the repetition configuration
        """

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # set number of repetitions
        if config['mode'] == CtaLib.RepetitionMode.FOREVER:
            self._pvs['Ctrl-Cycles-I'].put(0, wait=True)
        elif config['mode'] == CtaLib.RepetitionMode.NTIMES:
            self._pvs['Ctrl-Cycles-I'].put(config['n'], wait=True)
        else:
            RuntimeError('Invalid mode in repetition config received')

    def get_repetition_config(self):
        """
        Get the repetition configuration.

        This functions gets the current repetition configuration from the CTA
        and returns it as a dictionary. The format of the dictionary is the same
        as described for the function set_repetition_confg()

        Return
        config: dictionary describing the repetition configuration
        """

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # get number of repetitions
        repetitions = self._pvs['Ctrl-Cycles-I'].get()

        # prepare dictionary
        config = {}
        if repetitions == 0:
            config['mode'] = CtaLib.RepetitionMode.FOREVER
        else:
            config['mode'] = CtaLib.RepetitionMode.NTIMES
            config['n'] = repetitions

        return config

    class StartMode(IntEnum):
        """
        Enumeration of start modes
        """
        IMMEDIATE = 0
        MODULO = 1

    def set_start_config(self, *, config): # pylint: disable=R0912
        """
        Set the start configuration.

        This function uploads the start configuration to the IOC.
        The start configuration defines when the sequence is started on the IOC.
        The start configuration is defined with a dictionary.
        The key 'mode' is mandatory and can have the following values:
          * CtaLib.StartMode.IMMEDIATE
            The sequence is started a short, but undefined moment after
            CtaLib.start() has been called.
          * CtaLib.StartMode.MODULO
            After CtaLib.start() had been called, the sequence is started in the first
            machine pulse, where the expression
            (pulseId % divisor) - offset == 0 is true.
            In this mode the keys 'divisor' and 'offset' may be used to specify the
            corresponding values.
            Valid range for divisor is [1, 2^31-1].
            Valid range for offset is [0, 2^31-1].
            Furthermore divisor and offset depend on each other. The offset must be
            smaller than the divisor.

        Arguments
        config: dictionary describing the start configuration
        """

        logging.info('set_start_config() is running (config=%s)', config)

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # check arguments
        if 'mode' not in config:
            raise ValueError('Argument config does not contain mandatory key '
                             'mode')
        if (config['mode'] != CtaLib.StartMode.IMMEDIATE and
                config['mode'] != CtaLib.StartMode.MODULO):
            raise ValueError('Argument config contains invalid mode')
        if config['mode'] == CtaLib.StartMode.MODULO:
            if 'divisor' in config:
                if config['divisor'] <= 0 or config['divisor'] > 2**31-1:
                    raise ValueError('Argument config contains invalid divisor')
                if 'offset' not in config:
                    if config['divisor'] <= self._pvs['Ctrl-SCfgModOffset-I'].get():
                        raise ValueError('Argument config contains invalid divisor')
            if 'offset' in config:
                if config['offset'] < 0 or config['offset'] > 2**31-1:
                    raise ValueError('Argument config contains invalid offset')
                if 'divisor' in config:
                    if config['offset'] >= config['divisor']:
                        raise ValueError('Argument config contains invalid offset')
                else:
                    if config['offset'] >= self._pvs['Ctrl-SCfgModDivisor-I'].get():
                        raise ValueError('Argument config contains invalid offset')

        # caput values
        self._pvs['Ctrl-SCfgMode-I'].put(config['mode'].value)
        if config['mode'] == CtaLib.StartMode.MODULO:
            if 'divisor' in config:
                self._pvs['Ctrl-SCfgModDivisor-I'].put(config['divisor'])
            if 'offset' in config:
                self._pvs['Ctrl-SCfgModOffset-I'].put(config['offset'])

    def get_start_config(self):
        """
        Get the start configuration.

        This function downloads the current start configuration from the IOC
        and returns it as a dictionary. The format of the dictionary
        is the same as described for the function set_start_config().

        Return
        config: dictionary describing the start configuration
        """

        logging.info('get_start_config() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        config = {}

        mode = self._pvs['Ctrl-SCfgMode-I'].get()
        if mode == CtaLib.StartMode.IMMEDIATE:
            config['mode'] = CtaLib.StartMode.IMMEDIATE
        elif mode == CtaLib.StartMode.MODULO:
            config['mode'] = CtaLib.StartMode.MODULO
            config['divisor'] = self._pvs['Ctrl-SCfgModDivisor-I'].get()
            config['offset'] = self._pvs['Ctrl-SCfgModOffset-I'].get()
        else:
            raise RuntimeError('Unexpected mode received')

        logging.info('get_start_config() is done (config=%s)', config)

        return config

    def start(self):
        """
        Start CTA
        """

        logging.info('start() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # start
        self._pvs['Ctrl-Start-I'].put(1, wait=True)

        logging.info('start() is done')

    def stop(self):
        """
        Stop CTA

        """

        logging.info('stop() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        self._pvs['Ctrl-Stop-I'].put(1, wait=True)

        logging.info('stop() is done')

    def is_running(self):
        """
        Check if CTA is running

        Return
        True if CTA is running, False otherwise
        """

        logging.info('is_running() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # get status
        is_running = bool(self._pvs['Ctrl-IsRunning-O'].get() != 0)

        logging.info('is_running() is done')

        return is_running

    def get_started_at(self):
        """
        This function can be used to get the pulse id when the last sequence
        was started.

        Return
        started_at: pulse id when last sequence was started
        """

        logging.info('get_started_at() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # get number of repetitions
        started_at = self._pvs['Ctrl-StartedAt-O'].get()

        logging.info('get_started_at() is done')

        return int(started_at)

    def register_run_status_callback(self, callback, user_object=None):
        """
        This function can be used to register a callback function which is
        called if the run status of the sequence controller changed.
        Optionally a user object can be provided which will be passed to the callback
        function when it is called.

        The following argument will be passed to the callback function:
            data: dictionary where the key indicates which run status item
                  has changed and its new value

        Keep your callback function short.

        Mandatory arguments:
        callback: Function to be called.

        Optional arguments:
        user_object: object to be passed to callback function
        """

        rs_cb = {}
        rs_cb['callback'] = callback
        if user_object is not None:
            rs_cb['user_object'] = user_object
        self._run_status_callbacks.append(rs_cb)

    def register_repetition_config_callback(self, callback, user_object=None):
        """
        This function can be used to register a callback function which is
        called if the repetition configuration has changed.
        Optionally a user object can be provided which will be passed to the callback
        function when it is called.

        The callback function is called with a dictionary argument which has the
        same format as the dictionary returned by set_repetition_config().

        Keep your callback function short.

        Mandatory arguments:
        callback: Function to be called.

        Optional arguments:
        user_object: object to be passed to callback function
        """

        rep_config_cb = {}
        rep_config_cb['callback'] = callback
        if user_object is not None:
            rep_config_cb['user_object'] = user_object
        self._rep_config_callbacks.append(rep_config_cb)

    def register_start_config_callback(self, callback, user_object=None):
        """
        This function can be used to register a callback function which is
        called if the start config changed.
        Optionally a user object can be provided which will be passed to the callback
        function when it is called.

        The following argument will be passed to the callback function:
            config: dictionary where the key indicates which start config item
                    has changed and its new value

        Keep your callback function short.

        Mandatory arguments:
        callback: Function to be called.

        Optional arguments:
        user_object: object to be passed to callback function
        """

        sc_cb = {}
        sc_cb['callback'] = callback
        if user_object is not None:
            sc_cb['user_object'] = user_object
        self._start_config_callbacks.append(sc_cb)

    def register_sequence_callback(self, callback, user_object=None):
        """
        This function can be used to register a callback function which is
        called if the sequence on the IOC has changed.

        Refer to the upload method for a definition of a sequence.

        The following argument will be passed to the callback function:
            sequence: sequence containing the series which has changed

        Keep your callback function short.

        Mandatory arguments
        callback: Function to be called

        Optional arguments
        user_object: object to be passed to callback function
        """

        seq_cb = {}
        seq_cb['callback'] = callback
        if user_object is not None:
            seq_cb['user_object'] = user_object
        self._sequence_callbacks.append(seq_cb)

    def check_sequence(self, seq):
        """
        Check if a sequence is valid

        Arguments
        seq: The sequence to be checked.
                  A RuntimeError exception is thrown if the sequence is not valid.
                  Refer to the upload method for a definition of seq.
        """

        logging.info('check_sequence() is running')

        # check that seq has correct types and at least one series
        if not isinstance(seq, dict):
            raise RuntimeError("seq arg is not a dictionary")
        if not seq:
            raise RuntimeError("dictionary seq is empty")
        for key, series in seq.items():
            if not isinstance(key, int):
                raise RuntimeError("dictionary contains key value pair where key is"
                                   " not an int")
            if not isinstance(series, list):
                raise RuntimeError("dictionary contains key value pair where value is"
                                   " not a list")
            for item in series:
                if item not in (0, 1):
                    raise RuntimeError(
                        "dictionary contains key value pair where value is"
                        " is a list with at least one element which is not 0 or 1")

        # check that all series have same length
        length = len(seq[list(seq)[0]])
        for key, series in seq.items():
            if len(seq[key]) != length:
                raise RuntimeError(
                    "dictionary contains key value pair where at least"
                    " two values are lists with different length")

        # check that series are not too long
        length = len(seq[list(seq)[0]])
        if length > self._pvs['SerMaxLen-O'].get():
            raise RuntimeError(
                "dictionary contains key value pair where the values "
                "are lists with too many elements")

        logging.info('check_sequence() is done')

    def fill_empty_series(self, seq):
        """
        Fill the sequence such that all events are described

        Arguments
        seq: A sequence where some events might not be defined.

        Return
        seq: The sequence with all events defined.

        Refer to the upload method for a definition of seq.
        """


        logging.info('fill_empty_series() is running')

        length = len(list(seq.values())[0])
        for event_code in range(self._constants['event_code_range_base'],
                                self._constants['event_code_range_base'] +
                                self._constants['num_of_event_codes']):
            if event_code not in seq:
                seq[event_code] = [0] * length

        logging.info('fill_empty_series() is done')

        return seq

    def print(self, seq):
        """
        Print the sequence to std output

        Arguments
        seq: The sequence to be printed.
                  Refer to the upload method for a definition of seq.
        """

        logging.info('print() is running')
        logging.debug('print() prints: %s', str(seq))

        # check the sequence
        self.check_sequence(seq)

        length = len(seq[list(seq)[0]])

        print('      | <---------------- event -------------->')
        print('      | 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2')
        print('      | 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 1 1 1')
        print('pulse | 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9')
        print('-----------------------------------------------')
        for i in range(length):
            print(repr(i).rjust(5), '|', end='')
            for event_code in range(self._constants['event_code_range_base'],
                                    self._constants['event_code_range_base'] +
                                    self._constants['num_of_event_codes']):
                print("{state}".format(state=seq[event_code][i]).rjust(2), end='')
            print()

        logging.info('print() is done')

    def _run_status_callabck(self, **kwargs):
        """
        Callback function which is called when the run status PVs change the value.
        It is used to call user callback functions which registered for
        for this event.
        """
        logging.info('_run_status_callabck() is running (pv=%s, value=%s)',
                     kwargs['pvname'], str(kwargs['value']))

        if kwargs['pvname'] == self._pvs['Ctrl-IsRunning-O'].pvname:
            data = {'status': int(kwargs['value'])}
        elif kwargs['pvname'] == self._pvs['Ctrl-StartedAt-O'].pvname:
            data = {'started at': int(kwargs['value'])}
        else:
            raise RuntimeError('lib received status callback from unexpected pv')

        logging.info('calling run status callbacks next')
        for scb in self._run_status_callbacks:
            if 'user_object' in scb:
                scb['callback'](data, scb['user_object'])
            else:
                scb['callback'](data)
        logging.info('calling run status callbacks done')

    def _rep_config_callback(self, **kwargs):
        """
        Callback function which is called when the rep config PV changes the value.
        It is used to call user callback functions which registered for
        this event.
        """
        logging.info('_rep_config_callback() is running (pv=%s, value=%s)',
                     kwargs['pvname'], str(kwargs['value']))

        repetitions = int(kwargs['value'])
        config = {}
        if repetitions == 0:
            config['mode'] = CtaLib.RepetitionMode.FOREVER
        else:
            config['mode'] = CtaLib.RepetitionMode.NTIMES
            config['n'] = repetitions

        logging.info('calling rep config callbacks next')
        for rep_config_cb in self._rep_config_callbacks:
            if 'user_object' in rep_config_cb:
                rep_config_cb['callback'](config, rep_config_cb['user_object'])
            else:
                rep_config_cb['callback'](config)
        logging.info('calling rep config callbacks done')

    def _start_config_callback(self, **kwargs):
        """
        Callback function which is called when the start config PVs change the value.
        It is used to call user callback functions which registered for
        this event.
        """
        logging.info('_start_config_callback() is running (pv=%s, value=%s)',
                     kwargs['pvname'], str(kwargs['value']))

        if kwargs['pvname'] == self._pvs['Ctrl-SCfgMode-I'].pvname:
            if kwargs['value'] == CtaLib.StartMode.IMMEDIATE:
                config = {'mode': CtaLib.StartMode.IMMEDIATE}
            elif kwargs['value'] == CtaLib.StartMode.MODULO:
                config = {'mode': CtaLib.StartMode.MODULO}
            else:
                raise RuntimeError('Invalid mode received')
        elif kwargs['pvname'] == self._pvs['Ctrl-SCfgModDivisor-I'].pvname:
            config = {'divisor': int(kwargs['value'])}
        elif kwargs['pvname'] == self._pvs['Ctrl-SCfgModOffset-I'].pvname:
            config = {'offset': int(kwargs['value'])}
        else:
            raise RuntimeError('lib received status callback from unexpected pv')

        logging.info('calling start config callbacks next')
        for start_config_cb in self._start_config_callbacks:
            if 'user_object' in start_config_cb:
                start_config_cb['callback'](config, start_config_cb['user_object'])
            else:
                start_config_cb['callback'](config)
        logging.info('calling start config callbacks done')

    def _sequence_callback(self, **kwargs):
        """
        Callback function which is called when one of the PVs holding a series of
        the sequence changes the value. It is used to call user callback functions which
        registered for this event.
        """
        logging.info('_sequence_callback() is running (pv=%s, value=%s)',
                     kwargs['pvname'], str(kwargs['value']))

        # determine event number from pvname
        for idx, pv in enumerate(self._pvs['Data-I']): # pylint: disable=C0103
            if pv.pvname == kwargs['pvname']:
                event_number = self._constants['event_code_range_base'] + idx
                break

        # create sequence
        seq = {}
        seq[event_number] = numpy.atleast_1d(kwargs['value']).tolist()

        # call callbacks
        logging.info('calling sequence callbacks next')
        for seq_cb in self._sequence_callbacks:
            if 'user_object' in seq_cb:
                seq_cb['callback'](seq, seq_cb['user_object'])
            else:
                seq_cb['callback'](seq)
        logging.info('calling sequence callbacks done')

        logging.info('_sequence_callback() is done')

    def _connection_callback(self, **kwargs):
        """
        Callback function used internally to do connection status housekeeping

        Arguments
        pvname: name of PV for which the callback is called
        conn: status of the connection
        """

        logging.info('_connection_callback() is running (pvname=%s, conn=%s, '
                     'thread_id=%s)', kwargs['pvname'], repr(kwargs['conn']),
                     str(threading.get_ident()))

        # do connection housekeeping
        if kwargs['conn']:
            self._num_connected += 1
        else:
            self._num_connected -= 1
        logging.debug('_num_connected=%d', self._num_connected)

        # signal to other thread
        if self._num_connected == self._constants['num_of_pvs']:
            self._event.set()
        else:
            self._event.clear()

        logging.info('_connection_callback() is done')

# NOTE01
# This sleep is needed for the initial ca communication to be completed.
# If it is not there and the upload is called right after object creation,
# the number of elements in the PV has not arrived in python for all PVs.
# This leads to a fail of check_sequence().
