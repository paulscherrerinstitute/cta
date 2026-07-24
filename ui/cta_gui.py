from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys
from epics import PV
import numpy
import argparse
from enum import Enum
import logging
import time
import re

class SequenceState(Enum):
    EQUAL = 1
    UNEQUAL = 2
    UNKNOWN = 3
    CHECK = 4

class SequenceTableModel(QAbstractTableModel):
    
    def __init__(self, parent, sequence = [[]], headers = [], localEvents = []):
        QAbstractTableModel.__init__(self, parent)
        self.__parent = parent
        self.__sequence = sequence
        self.__headers = headers
        self.__columnMap = {'stepOff': 0, 'startOff': 1, 'evtCode': 2}
        self.__localEvents = localEvents
        self.__serMaxLen = 0

    def rowCount(self, parent):
        return len(self.__sequence)
    
    def columnCount(self, parent):
        return len(self.__columnMap)

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role):
        
        if role == Qt.EditRole:
            row = index.row()
            column = index.column()
            return self.__sequence[row][column]
        
        if role == Qt.DisplayRole:
            row = index.row()
            column = index.column()
            value = self.__sequence[row][column]
            
            return value

    # This method is called by the view if the user entered new data
    #
    # index: index at which to change the data
    # value: new value for the data        
    # role : edit role
    def setData(self, index, value, role = Qt.EditRole):

        row = index.row()
        column = index.column()
        
        if column == self.__columnMap['evtCode']:
            rc, uIndTopLeft, uIndBotRight = self.setDataEvtCode(index, value, role)
        
        if column == self.__columnMap['stepOff']:
            rc, uIndTopLeft, uIndBotRight = self.setDataStepOff(index, value, role)
        
        if column == self.__columnMap['startOff']:
            rc, uIndTopLeft, uIndBotRight = self.setDataStartOff(index, value, role)
        
        if not rc:
            return False

        # update view
        self.dataChanged.emit(uIndTopLeft, uIndBotRight)

        self.__parent.update_equal_not_equal[object].emit(SequenceState.UNEQUAL)

        return True

    def setDataEvtCode(self, index, value, role):

        if role == Qt.EditRole:

            row = index.row()
            column = index.column()

            # verify value
            if not (value in self.__localEvents):
                return False, 0, 0
            
            # set value
            self.__sequence[row][column] = value

            # return index for view update
            return True, index, index

    def setDataStepOff(self, index, value, role):
        
        logging.info('SequenceTableModel.setDataStepOff() is running')
        
        if role == Qt.EditRole:

            row = index.row()
            column = index.column()
            logging.debug('row=' + str(row) + ' column=' + str(column))

            # verify value

            ## value need to be in the allowed range
            if value < 0 or value >= self.__serMaxLen:
                return False, 0, 0

            ## the sum of all step offsets may not be bigger
            ## than the maximum sequence length
            sumOff = 0
            for i in range(self.rowCount(self)):
                if i != row:
                    sumOff += self.__sequence[i][column]
            if sumOff + value >= self.__serMaxLen:
                logging.debug(sumOff+value)
                return False, 0, 0
            
            # set value
            self.__sequence[row][column] = value

            # update dependent data
            self.startOffFromStepOff();

            logging.info('SequenceTableModel.setDataStepOff() is done')

            return True, index, index

        logging.info('SequenceTableModel.setDataStepOff() is done')
            
    def setDataStartOff(self, index, value, role):
        
        logging.info('SequenceTableModel.setDataStartOff() is running')
        
        if role == Qt.EditRole:

            row = index.row()
            column = index.column()
            logging.debug('row=' + str(row) + ' column=' + str(column))

            # verify value

            ## start offset value need to be in the allowed range
            if value < 0 or value >= self.__serMaxLen:
                return False, 0, 0

            ## check if row and column are in the valid range
            if row < 0 or column < 0 or column > 2:
                return False, 0, 0

            ## if it is not the first row the start offset must be
            ## equal or bigger than the start offset of the previous row
            if row > 0:
                if value < self.__sequence[row - 1][column]:
                    return False, 0, 0

            ## if it is not the last row, the start offset must be smaller
            ## than the start offset of the next row
            if row < self.rowCount(self) - 1:
                if value > self.__sequence[row + 1][column]:
                    return False, 0, 0

            # set value
            self.__sequence[row][column] = value

            # update dependent data
            self.stepOffFromStartOff();

            logging.info('SequenceTableModel.setDataStartOff() is done')

            return True, index, index
            
        logging.info('SequenceTableModel.setDataStartOff() is done')

    def headerData(self, section, orientation, role):
        
        if role == Qt.DisplayRole:
            
            if orientation == Qt.Horizontal:
                
                if section < len(self.__headers):
                    return self.__headers[section]
                else:
                    return "not available"
            else:
                return str(section)

    # row: row index of first row to be inserted
    #      row = 0 => prepend
    #      row = rowCount() => append
    # count: number of rows to be inserted
    def insertRows(self, row, count, parent = QModelIndex()):

        logging.info('SequenceTableModel.insertRows() is running')

        logging.debug('row=' + str(row) + ' count=' + str(count))

        self.beginInsertRows(parent, row, row + count - 1)
        
        # insert data
        for i in range(count):
            seq_idx_before = row + i
            logging.debug('seq_idx_before=' + str(seq_idx_before))
            if seq_idx_before == 0: # empty or prepend
                self.__sequence.insert(seq_idx_before,
                  [0, 0, self.__localEvents[0]])
            else:
                self.__sequence.insert(seq_idx_before,
                  [0, self.__sequence[seq_idx_before - 1]
                  [self.__columnMap['startOff']], self.__localEvents[0]])

        logging.debug(self.__sequence)
        
        self.endInsertRows()
        
        self.__parent.update_equal_not_equal[object].emit(SequenceState.UNEQUAL)

        logging.info('SequenceTableModel.insertRows() is done')

        return True

    # row: index of first row to be removed
    # count: number of rows to be removed
    def removeRowsKeepStepOff(self, row, count, parent = QModelIndex()):

        logging.info('SequenceTableModel.removeRowsKeepStepOff is running')

        logging.debug('row=' + str(row) + ' count=' + str(count))
        
        first = row
        last = first + count - 1

        if first < 0:
            return False
        if last >= self.rowCount(self):
            return False

        self.beginRemoveRows(parent, first, last)

        self.__sequence[first:last+1] = []
        self.startOffFromStepOff()

        logging.debug(self.__sequence)

        self.endRemoveRows()
        
        self.__parent.update_equal_not_equal[object].emit(SequenceState.UNEQUAL)

        logging.info('SequenceTableModel.removeRowsKeepStepOff is done')

        return True

    # row: index of first row to be removed
    # count: number of rows to be removed
    def removeRowsKeepStartOff(self, row, count, parent = QModelIndex()):

        logging.info('SequenceTableModel.removeRowsKeepStartOff is running')

        logging.debug('row=' + str(row) + ' count=' + str(count))
        
        first = row
        last = first + count - 1

        if first < 0:
            return False
        if last >= self.rowCount(self):
            return False

        self.beginRemoveRows(parent, first, last)

        self.__sequence[first:last+1] = []
        self.stepOffFromStartOff()

        logging.debug(self.__sequence)

        self.endRemoveRows()
        
        self.__parent.update_equal_not_equal[object].emit(SequenceState.UNEQUAL)

        logging.info('SequenceTableModel.removeRowsKeepStartOff is done')

        return True

    def startOffFromStepOff(self):
        
        cumStepOff = 0

        for i in range(len(self.__sequence)):
            cumStepOff += self.__sequence[i][self.__columnMap['stepOff']]
            self.__sequence[i][self.__columnMap['startOff']] = cumStepOff

    def stepOffFromStartOff(self):
        
        lastOff = 0

        for i in range(len(self.__sequence)):
            currOff = self.__sequence[i][self.__columnMap['startOff']]
            self.__sequence[i][self.__columnMap['stepOff']] = currOff - lastOff
            lastOff = currOff

    def setMaxLength(self, maxLen):
        self.__serMaxLen = maxLen

    def getMaxLength(self):
        return self.serMaxLen

    def getSeries(self):

        logging.info('SequenceTableModel.getSeries() is running')

        logging.debug(self.__sequence)

        # find the length of the series
        if self.rowCount(self) == 0:
            seriesLength = 1
        else:
            seriesLength = self.__sequence[-1][self.__columnMap['startOff']] + 1

        # create series and init it with zeros
        series = [None] * len(self.__localEvents)
        for i in range(len(self.__localEvents)):
            series[i] = [0] * seriesLength

        # transform table to series
        for row in range(len(self.__sequence)):
            step_offset = self.__sequence[row][self.__columnMap['startOff']]
            event_code = self.__sequence[row][self.__columnMap['evtCode']] 
            series[self.__localEvents.index(event_code)][step_offset] = 1

        logging.debug(series)

        logging.info('SequenceTableModel.getSeries() is done')

        return series

    def setSeries(self, series):

        logging.info('SequenceTableModel.setSeries() is running')

        logging.debug(series)

        # normalize input ( [array(0)], [0] and None depending on status...)
        normalised = []
        for s in series:
            if s is None:
                normalised.append([])
            else:
                normalised.append([
                    int(numpy.asarray(x).item()) 
                    for x in s 
                    if x is not None and numpy.asarray(x).size==1
                ])

        series = normalised

        # init sequence
        s = 0

        for i in range(len(self.__localEvents)):
            s += sum(series[i])
        
        self.__sequence = [None] * s
        for i in range(s):
            self.__sequence[i] = [None] * 3

        # loop over series
        row = 0
        
        for i in range(len(series[0])):

            # loop over local events
            for k in range(len(self.__localEvents)):

                # add row if enabled
                if series[k][i]:
                    if row == 0:
                        self.__sequence[row][self.__columnMap['stepOff']] = i
                    else:
                        self.__sequence[row][self.__columnMap['stepOff']] = i - self.__sequence[row-1][self.__columnMap['startOff']]
                    self.__sequence[row][self.__columnMap['startOff']] = i
                    self.__sequence[row][self.__columnMap['evtCode']] = self.__localEvents[k]
                    row += 1

        logging.debug(self.__sequence)

        logging.info('SequenceTableModel.setSeries() is done')

class SequenceTableView(QTableView):
    
    def __init__(self, parent, model):
        super(SequenceTableView, self).__init__(parent)
        self.model = model
        self.setModel(model)

    def sizeHint(self):
        horizontal = self.horizontalHeader()
        vertical = self.verticalHeader()
        frame = self.frameWidth() * 2
        return QSize(horizontal.length() + vertical.width() + frame,
          vertical.length() *10 + horizontal.height() + frame)

    def contextMenuEvent(self, event):

      logging.info("SequenceTableView.contextMenuEvent() is running")
      
      position = event.pos()
      column = self.columnAt(position.x())
      row = self.rowAt(position.y())

      self.menu = QMenu(self)

      actionAddRow = QAction('insert row', self)
      actionAddRow.triggered.connect(lambda: self.insertRow(row))
      self.menu.addAction(actionAddRow)

      actionRmRowKeepStepOff = QAction('remove row (keep step offsets)', self)
      actionRmRowKeepStepOff.triggered.connect(lambda: self.removeRowKeepStepOff(row))
      self.menu.addAction(actionRmRowKeepStepOff)

      actionRmRowKeepStartOff = QAction('remove row (keep start offsets)', self)
      actionRmRowKeepStartOff.triggered.connect(lambda: self.removeRowKeepStartOff(row))
      self.menu.addAction(actionRmRowKeepStartOff)

      self.menu.popup(QCursor.pos())

      logging.info("SequenceTableView.contextMenuEvent() is done")

    def insertRow(self, row):

      logging.info("SequenceTableView.insertRow() is running")

      self.model.insertRows(row + 1, 1)
      #self.adjustSize()

      logging.info("SequenceTableView.insertRow() is done")

    def removeRowKeepStepOff(self, row):

      logging.info("SequenceTableView.removeRowKeepStepOff() is running")

      self.model.removeRowsKeepStepOff(row, 1)
      #self.adjustSize()

      logging.info("SequenceTableView.removeRowKeepStepOff() is done")

    def removeRowKeepStartOff(self, row):

      logging.info("SequenceTableView.removeRowKeepStartOff() is running")

      self.model.removeRowsKeepStartOff(row, 1)
      #self.adjustSize()

      logging.info("SequenceTableView.removeRowKeepStartOff() is done")

class SequenceDialog(QWidget):

    # Create signal objects
    set_max_length = pyqtSignal(object)
    update_rep_config = pyqtSignal(object)
    update_equal_not_equal = pyqtSignal([object], [object, object, object])
    update_run_status = pyqtSignal(object, object)
    update_start_config = pyqtSignal(object, object, object)
    upload_sequence = pyqtSignal()       

    def __init__(self, args):

        super(SequenceDialog, self).__init__()

        # save args for later
        self.args = args 

        # init state
        self.divisor = 1
        self.offset = 0

        # create widgets
        self.createWidgets()

        # connect signals to slots
        self.__btnDown.clicked.connect(self.btnDownAction)
        self.__btnUp.clicked.connect(self.btnUpAction)
        self.__btnStart.clicked.connect(self.btnStartAction)
        self.__btnStop.clicked.connect(self.btnStopAction)
        self.__sb_repetitions.editingFinished.connect(self.rep_config_changed)
        self.__rbtn_forever.clicked.connect(self.rep_config_changed)
        self.__rbtn_repetitions.clicked.connect(self.rep_config_changed)
        self.__rbtn_immediatly.clicked.connect(self.start_config_changed)
        self.__rbtn_modulo.clicked.connect(self.start_config_changed)
        self.__leditDivisor.editingFinished.connect(self.start_config_changed)
        self.__leditOffset.editingFinished.connect(self.start_config_changed)
        self.__btnInsertRow.clicked.connect(self.btnInsertRowAction)
        self.__btnRemoveRow.clicked.connect(self.btnRemoveRowAction)
        self.set_max_length.connect(self.__update_max_length)
        self.update_rep_config.connect(self.__update_rep_config)
        self.update_equal_not_equal.connect(self.__update_equal_not_equal)
        self.update_run_status.connect(self.__update_run_status)
        self.update_start_config.connect(self.__update_start_config)
        self.upload_sequence.connect(self.__upload_sequence)

        # create pv objects
        self.pvSerMaxLen = PV(args.device + ':SerMaxLen-O',
                              callback=self.__on_pv_max_length_change)
        self.pvLength = PV(args.device + ':seq0Ctrl-Length-I')
        self.pvCycles = PV(args.device + ':seq0Ctrl-Cycles-I',
                           callback=self.__on_pvs_rep_conf_change)
        self.pvSeq0Ser0 = PV(
                args.device + ':seq0Ser0-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser1 = PV(
                args.device + ':seq0Ser1-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser2 = PV(
                args.device + ':seq0Ser2-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser3 = PV(
                args.device + ':seq0Ser3-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser4 = PV(
                args.device + ':seq0Ser4-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser5 = PV(
                args.device + ':seq0Ser5-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser6 = PV(
                args.device + ':seq0Ser6-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser7 = PV(
                args.device + ':seq0Ser7-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser8 = PV(
                args.device + ':seq0Ser8-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser9 = PV(
                args.device + ':seq0Ser9-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser10 = PV(
                args.device + ':seq0Ser10-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser11 = PV(
                args.device + ':seq0Ser11-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser12 = PV(
                args.device + ':seq0Ser12-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser13 = PV(
                args.device + ':seq0Ser13-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser14 = PV(
                args.device + ':seq0Ser14-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser15 = PV(
                args.device + ':seq0Ser15-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser16 = PV(
                args.device + ':seq0Ser16-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser17 = PV(
                args.device + ':seq0Ser17-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser18 = PV(
                args.device + ':seq0Ser18-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvSeq0Ser19 = PV(
                args.device + ':seq0Ser19-Data-I',
                callback=self.__on_pvs_seq_change,
                auto_monitor = True
        )
        self.pvStart = PV(args.device + ':seq0Ctrl-Start-I')
        self.pvStop = PV(args.device + ':seq0Ctrl-Stop-I')
        self.pvStatus = PV(args.device + ':seq0Ctrl-IsRunning-O',
                           callback=self.__on_pvs_run_status_change)
        self.pvStartedAt = PV(args.device + ':seq0Ctrl-StartedAt-O',
                              callback=self.__on_pvs_run_status_change)
        self.pvSCfgMode = PV(args.device + ':seq0Ctrl-SCfgMode-I',
                             callback=self.__on_pvs_start_config_change)
        self.pvSCfgModDivisor = PV(args.device + ':seq0Ctrl-SCfgModDivisor-I',
                                   callback=self.__on_pvs_start_config_change)
        self.pvSCfgModOffset = PV(args.device + ':seq0Ctrl-SCfgModOffset-I',
                                  callback=self.__on_pvs_start_config_change)

        # wait until all pvs have an initial values
        # (and signals to process these values have been send)
        time.sleep(2)

        # ensure sequence on ioc is uploaded on gui start up
        # We do this with a timer to get the request to the gui
        # event queue.
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.__upload_sequence)
        self.timer.start(10)

    def createWidgets(self):

        # set GUI title
        self.setWindowTitle("CTA GUI " + self.args.esx)

        # create model
        headers = ["Step Offset", "Start Offset", "Event Codes"]
        initialSequence = [[0, 0, 200]]
        self.__localEvents = range(200, 220)
        self.__model = SequenceTableModel(self,
            initialSequence, headers, self.__localEvents)

        # create top layouts
        horizontal_layout = QHBoxLayout()
        vertical0_layout = QVBoxLayout()
        vertical1_layout = QVBoxLayout()

        # sequence upload/download group
        self.__labelTable = QLabel('sequence in table')
        self.__labelCompare = QLabel()
        self.__labelCompare.setAlignment(Qt.AlignCenter);
        self.__labelIoc = QLabel('sequence on IOC')
        self.__btnDown = QPushButton('-->', self)
        self.__btnUp = QPushButton('<--', self)
        self.__grpb_seq_load = QGroupBox('sequence upload/download')
        vbl = QVBoxLayout()
        hbl = QHBoxLayout()
        hbl.addWidget(self.__labelTable)
        hbl.addWidget(self.__labelCompare)
        hbl.addWidget(self.__labelIoc)
        vbl.addLayout(hbl)
        vbl.addWidget(self.__btnDown)
        vbl.addWidget(self.__btnUp)
        self.__grpb_seq_load.setLayout(vbl)
        vertical0_layout.addWidget(self.__grpb_seq_load)

        # sequence definition group
        self.__tableView = SequenceTableView(self, self.__model)
        #self.__tableView.resizeColumnsToContents()
        self.__grpb_table = QGroupBox('sequence definition')
        self.__btnInsertRow = QPushButton('insert row')
        self.__btnRemoveRow = QPushButton('remove row')
        vbl = QVBoxLayout()
        vbl.addWidget(self.__tableView)
        hbl = QHBoxLayout()
        hbl.addWidget(self.__btnInsertRow)
        hbl.addWidget(self.__btnRemoveRow)
        vbl.addLayout(hbl)
        self.__grpb_table.setLayout(vbl)
        vertical0_layout.addWidget(self.__grpb_table)

        # run status group
        self.__btnStart = QPushButton('start', self)
        self.__btnStop = QPushButton('stop', self)
        self.__labelStatus = QLabel('status', self)
        self.__leditStatus = QLineEdit(self)
        self.__labelStartedAt = QLabel('started at', self)
        self.__leditStartedAt = QLineEdit(self)
        self.__leditStartedAt.setDisabled(True)
        self.__grpb_run_status = QGroupBox('run status', self)
        self.__leditStatus.setDisabled(True)
        vbl = QVBoxLayout()
        hbl = QHBoxLayout()
        hbl.addWidget(self.__btnStart)
        hbl.addWidget(self.__btnStop)
        vbl.addLayout(hbl)
        hbl = QHBoxLayout()
        hbl.addWidget(self.__labelStatus)
        hbl.addWidget(self.__leditStatus)
        vbl.addLayout(hbl)
        hbl = QHBoxLayout()
        hbl.addWidget(self.__labelStartedAt)
        hbl.addWidget(self.__leditStartedAt)
        vbl.addLayout(hbl)
        self.__grpb_run_status.setLayout(vbl)
        vertical1_layout.addWidget(self.__grpb_run_status)

        # repetition configuration group
        self.__rbtn_repetitions = QRadioButton('number of repetitions')
        self.__sb_repetitions = QSpinBox()
        self.__rbtn_forever = QRadioButton('forever')
        self.__rbtn_repetitions.setChecked(True)
        self.__grpb_repetitions = QGroupBox('repetition configuration', self)
        self.__sb_repetitions.setRange(1, 65536) # 16 bit
        hbl = QHBoxLayout()
        vbl = QVBoxLayout()
        hbl.addWidget(self.__rbtn_repetitions)
        hbl.addWidget(self.__sb_repetitions)
        vbl.addLayout(hbl)
        vbl.addWidget(self.__rbtn_forever)
        self.__grpb_repetitions.setLayout(vbl)
        vertical1_layout.addWidget(self.__grpb_repetitions)

        # start configuration group
        self.__rbtn_immediatly = QRadioButton('start immediately')
        self.__rbtn_modulo = QRadioButton('start if ((pulseId % divisor) - offset == 0)')
        self.__spacerItemDivisor = QSpacerItem(20, 10)
        self.__labelDivisor = QLabel('Divisor', self)
        self.__leditDivisor = QLineEdit(self)
        self.__spacerItemOffset = QSpacerItem(20, 10)
        self.__labelOffset = QLabel('Offset', self)
        self.__leditOffset = QLineEdit(self)
        self.__grpb_start_config = QGroupBox("start configuration", self)
        vbl = QVBoxLayout()
        vbl.addWidget(self.__rbtn_immediatly)
        vbl.addWidget(self.__rbtn_modulo)
        hbl = QHBoxLayout()
        hbl.addItem(self.__spacerItemDivisor)
        hbl.addWidget(self.__labelDivisor)
        hbl.addWidget(self.__leditDivisor)
        vbl.addLayout(hbl)
        hbl = QHBoxLayout()
        hbl.addItem(self.__spacerItemOffset)
        hbl.addWidget(self.__labelOffset)
        hbl.addWidget(self.__leditOffset)
        vbl.addLayout(hbl)
        self.__grpb_start_config.setLayout(vbl)
        vertical1_layout.addWidget(self.__grpb_start_config)

        horizontal_layout.addLayout(vertical0_layout)
        horizontal_layout.addLayout(vertical1_layout)

        self.setLayout(horizontal_layout)

    def __on_pv_max_length_change(self, pvname=None, value=None, char_value=None,
        **kw):
        """
        Refer to NOTE01
        """
        logging.info('SequenceDialog.__on_pv_max_length_change() is running')

        logging.debug('pv %s has changed, new value=%s', pvname, char_value)
        self.set_max_length.emit(value)

        logging.info('SequenceDialog.__on_pv_max_length_change() is done')

    def __on_pvs_rep_conf_change(self, pvname=None, value=None, char_value=None,
        **kw):
        """
        Refer to NOTE01
        """
        logging.info('SequenceDialog.__on_pvs_rep_conf_change() is running')

        logging.debug('pv %s has changed, new value=%s', pvname, char_value)
        self.update_rep_config.emit(value)

        logging.info('SequenceDialog.__on_pvs_rep_conf_change() is done')

    def __on_pvs_seq_change(self, pvname=None, value=None, char_value=None,
        **kw):
        """
        Refer to NOTE01
        """

        logging.info('SequenceDialog.__on_pvs_seq_change() is running')

        # extract which series has changed
        po = re.compile('.*seq[0-9]*Ser([0-9]*)-Data-I')
        mo = po.search(pvname)
        series_index = int(mo.group(1))
        logging.debug('pv %s has changed, new value=%s', pvname , str(value))

        # transform value to list
        if hasattr(value, "__len__"):
            series_ioc = [int(numpy.asarray(x).item()) for x in value] 
        else:
            series_ioc = [int(numpy.asarray(value).item())]

        self.update_equal_not_equal[object].emit(SequenceState.UNEQUAL)

        logging.info('SequenceDialog.__on_pvs_seq_change() is done')

    def __on_pvs_run_status_change(self, pvname=None, value=None, char_value=None,
        **kw):
        """
        Refer to NOTE01
        """

        logging.info('SequenceDialog.__on_pvs_run_status_change() is running')

        logging.debug('pv %s has changed, new value=%s', pvname, char_value)
        self.update_run_status.emit(pvname, value)

        logging.info('SequenceDialog.__on_pvs_run_status_change() is done')

    def __on_pvs_start_config_change(self, pvname=None, value=None, char_value=None,
        **kw):
        """
        Refer to NOTE01
        """
        logging.info('SequenceDialog.__on_pvs_start_config_change() is running')

        logging.debug('pv %s has changed, new value=%s', pvname, char_value)
        self.update_start_config.emit(pvname, value, char_value)

        logging.info('SequenceDialog.__on_pvs_start_config_change() is done')

    def btnDownAction(self):
        """
        Refer to NOTE02
        """

        logging.info('SequenceDialog.btnDownAction() is running')

        series = self.__model.getSeries()

        self.pvLength.put(len(series[0]))

        self.pvSeq0Ser0.put(numpy.array(series[0]), wait=True)
        self.pvSeq0Ser1.put(numpy.array(series[1]), wait=True)
        self.pvSeq0Ser2.put(numpy.array(series[2]), wait=True)
        self.pvSeq0Ser3.put(numpy.array(series[3]), wait=True)
        self.pvSeq0Ser4.put(numpy.array(series[4]), wait=True)
        self.pvSeq0Ser5.put(numpy.array(series[5]), wait=True)
        self.pvSeq0Ser6.put(numpy.array(series[6]), wait=True)
        self.pvSeq0Ser7.put(numpy.array(series[7]), wait=True)
        self.pvSeq0Ser8.put(numpy.array(series[8]), wait=True)
        self.pvSeq0Ser9.put(numpy.array(series[9]), wait=True)
        self.pvSeq0Ser10.put(numpy.array(series[10]), wait=True)
        self.pvSeq0Ser11.put(numpy.array(series[11]), wait=True)
        self.pvSeq0Ser12.put(numpy.array(series[12]), wait=True)
        self.pvSeq0Ser13.put(numpy.array(series[13]), wait=True)
        self.pvSeq0Ser14.put(numpy.array(series[14]), wait=True)
        self.pvSeq0Ser15.put(numpy.array(series[15]), wait=True)
        self.pvSeq0Ser16.put(numpy.array(series[16]), wait=True)
        self.pvSeq0Ser17.put(numpy.array(series[17]), wait=True)
        self.pvSeq0Ser18.put(numpy.array(series[18]), wait=True)
        self.pvSeq0Ser19.put(numpy.array(series[19]), wait=True)

        # 'hacky' approach to make sure all sequences were uploaded
        QTimer.singleShot(600, self.__upload_sequence)

        logging.info('SequenceDialog.btnDownAction() is done')

    def btnUpAction(self):
        """
        Refer to NOTE02
        """
        logging.info('SequenceDialog.btnUpAction() is running')

        self.__upload_sequence()

        logging.info('SequenceDialog.btnUpAction() is done')

    def btnStartAction(self):
        """
        Refer to NOTE02
        """
        logging.info('SequenceDialog.btnStartAction() is running')

        self.pvStart.put(1)

        logging.info('SequenceDialog.btnStartAction() is done')

    def btnStopAction(self):
        """
        Refer to NOTE02
        """
        logging.info('SequenceDialog.btnStopAction() is running')

        self.pvStop.put(1)

        logging.info('SequenceDialog.btnStopAction() is done')

    def rep_config_changed(self):
        """
        Refer to NOTE02
        """

        logging.info('SequenceDialog.rep_config_changed() is running')

        if self.__rbtn_forever.isChecked():
            repetitions = 0
        else:
            repetitions = self.__sb_repetitions.value()

        if repetitions != self.pvCycles.get():
            logging.debug('put rep config cycles=%d to pv', repetitions)
            self.pvCycles.put(repetitions)

        logging.info('SequenceDialog.rep_config_changed() is done')

    def start_config_changed(self):
        """
        Refer to NOTE02
        """

        logging.info('SequenceDialog.start_config_changed() is running')

        if self.__rbtn_immediatly.isChecked():
            if self.pvSCfgMode.get() != 0:
                logging.debug('put start config mode=0 to pv')
                self.pvSCfgMode.put(0)

        if self.__rbtn_modulo.isChecked():
            if self.pvSCfgMode.get() != 1:
                logging.debug('put start config mode=1 to pv')
                self.pvSCfgMode.put(1)

        # validate divisor and offset user input (int conversion)
        try:
            divisor = int(self.__leditDivisor.text())
        except ValueError:
            divisor = self.divisor
            self.__leditDivisor.setText(str(divisor))
        try:
            offset = int(self.__leditOffset.text())
        except ValueError:
            offset = self.offset
            self.__leditOffset.setText(str(offset))

        # divisor ---------------------
        # validate user input (value)
        if divisor <= 0 or divisor <= offset:
            divisor = self.divisor
            self.__leditDivisor.setText(str(divisor))
        # update state and caput
        self.divisor = divisor
        if divisor != self.pvSCfgModDivisor.get():
            logging.debug('put start config divisor=%s to pv', divisor)
            self.pvSCfgModDivisor.put(divisor)

        # offset ----------------------
        # validate user input (value)
        if offset < 0 or offset >= divisor:
            offset = self.offset
            self.__leditOffset.setText(str(offset))
        # update state and caput
        self.offset = offset
        if offset != self.pvSCfgModOffset.get():
            logging.debug('put start config offset=%s to pv', offset)
            self.pvSCfgModOffset.put(offset)

        logging.info('SequenceDialog.start_config_changed() is done')

    def btnInsertRowAction(self):
        """
        Refer to NOTE02
        """
        logging.info('SequenceDialog.btnInsertRowAction() is running')

        self.__model.insertRows(self.__model.rowCount(self), 1)

        logging.info('SequenceDialog.btnInsertRowAction() is done')

    def btnRemoveRowAction(self):
        """
        Refer to NOTE02
        """
        logging.info('SequenceDialog.btnRemoveRowAction() is running')

        self.__model.removeRowsKeepStepOff(self.__model.rowCount(self) - 1, 1)

        logging.info('SequenceDialog.btnRemoveRowAction() is done')

    def __update_max_length(self, max_length):
        """
        Refer to NOTE02
        """

        logging.info('SequenceDialog.__update_max_length() is running')
        self.__model.setMaxLength(max_length)
        logging.info('SequenceDialog.__update_max_length() is done')

    def __update_rep_config(self, value):
        """
        Refer to NOTE02
        """

        logging.info('SequenceDialog.__update_rep_config() is running')

        if value == 0:
            self.__rbtn_forever.setChecked(True)
            logging.debug('updating radio buttons')
        else:
            logging.debug('updating radio buttons and spin box, value=%s', value)
            self.__rbtn_repetitions.setChecked(True)
            self.__sb_repetitions.setValue(value)

        logging.info('SequenceDialog.__update_rep_config() is done')

    def __upload_sequence(self):
        """
        Refer to NOTE02
        """

        logging.info('SequenceDialog.__upload_sequence() is running')

        series = [None] * len(self.__localEvents)

        length = self.pvLength.get()
        
        if length is None:
            logging.warning("pvLength not available yet, retrying in 500 ms")
            QTimer.singleShot(500, self.__upload_sequence)
            return

        if  length > 1:
            series[0] = self.pvSeq0Ser0.get().tolist()
            series[1] = self.pvSeq0Ser1.get().tolist()
            series[2] = self.pvSeq0Ser2.get().tolist()
            series[3] = self.pvSeq0Ser3.get().tolist()
            series[4] = self.pvSeq0Ser4.get().tolist()
            series[5] = self.pvSeq0Ser5.get().tolist()
            series[6] = self.pvSeq0Ser6.get().tolist()
            series[7] = self.pvSeq0Ser7.get().tolist()
            series[8] = self.pvSeq0Ser8.get().tolist()
            series[9] = self.pvSeq0Ser9.get().tolist()
            series[10] = self.pvSeq0Ser10.get().tolist()
            series[11] = self.pvSeq0Ser11.get().tolist()
            series[12] = self.pvSeq0Ser12.get().tolist()
            series[13] = self.pvSeq0Ser13.get().tolist()
            series[14] = self.pvSeq0Ser14.get().tolist()
            series[15] = self.pvSeq0Ser15.get().tolist()
            series[16] = self.pvSeq0Ser16.get().tolist()
            series[17] = self.pvSeq0Ser17.get().tolist()
            series[18] = self.pvSeq0Ser18.get().tolist()
            series[19] = self.pvSeq0Ser19.get().tolist()
        elif length == 1:
            series[0] = [self.pvSeq0Ser0.get()]
            series[1] = [self.pvSeq0Ser1.get()]
            series[2] = [self.pvSeq0Ser2.get()]
            series[3] = [self.pvSeq0Ser3.get()]
            series[4] = [self.pvSeq0Ser4.get()]
            series[5] = [self.pvSeq0Ser5.get()]
            series[6] = [self.pvSeq0Ser6.get()]
            series[7] = [self.pvSeq0Ser7.get()]
            series[8] = [self.pvSeq0Ser8.get()]
            series[9] = [self.pvSeq0Ser9.get()]
            series[10] = [self.pvSeq0Ser10.get()]
            series[11] = [self.pvSeq0Ser11.get()]
            series[12] = [self.pvSeq0Ser12.get()]
            series[13] = [self.pvSeq0Ser13.get()]
            series[14] = [self.pvSeq0Ser14.get()]
            series[15] = [self.pvSeq0Ser15.get()]
            series[16] = [self.pvSeq0Ser16.get()]
            series[17] = [self.pvSeq0Ser17.get()]
            series[18] = [self.pvSeq0Ser18.get()]
            series[19] = [self.pvSeq0Ser19.get()]
        else:
            for i in range(len(self.__localEvents)):
                series[i] = [0]

        self.__model.setSeries(series)

        self.__model.beginResetModel()
        self.__model.endResetModel()

        self.__update_equal_not_equal(SequenceState.EQUAL)

        logging.info('SequenceDialog.__upload_sequence() is done')


    def __update_equal_not_equal(self, state, series_index=None, series_ioc=None):
        """
        Refer to NOTE02
        """
        
        logging.info('SequenceDialog.__update_equal_not_equal() is running')

        if state is SequenceState.CHECK:
            logging.debug('__update_equal_not_equal() state=%s, series_index=%s, series_ioc=%s',
                           state, series_index, series_ioc)
            # get series currently in model
            if self.__model.getSeries()[series_index] == series_ioc:
                state = SequenceState.EQUAL
            else:
                state = SequenceState.UNEQUAL

        if state is SequenceState.EQUAL:
            logging.debug('__update_equal_not_equal() state=EQUAL')
            self.__labelCompare.setText('  ==  ')
            self.__labelCompare.setStyleSheet("QLabel { background-color : green; color : black; }");
        elif state is SequenceState.UNEQUAL:
            logging.debug('__update_equal_not_equal() state=UNEQUAL')
            self.__labelCompare.setText('  !=  ')
            self.__labelCompare.setStyleSheet("QLabel { background-color : red; color : black; }");
        elif state is SequenceState.UNKNOWN:
            logging.debug('__update_equal_not_equal() state=UNKNOWN')
            self.__labelCompare.setText('  ??  ')
            self.__labelCompare.setStyleSheet("QLabel { background-color : orange; color : black; }");
        else:
            raise RunTimeError('unexpected state received')

        logging.info('SequenceDialog.__update_equal_not_equal() is done')

    def __update_run_status(self, pvname, value):
        """
        Refer to NOTE02
        """

        logging.info('SequenceDialog._update_run_status() is running')

        if pvname == self.pvStatus.pvname:
            if value == 0:
                self.__leditStatus.setText('stopped')
                self.__grpb_repetitions.setDisabled(False)
                self.__grpb_start_config.setDisabled(False)
                self.__btnStart.setDisabled(False)
                self.__btnStop.setDisabled(True)
            else:
                self.__leditStatus.setText('running')
                self.__grpb_repetitions.setDisabled(True)
                self.__grpb_start_config.setDisabled(True)
                self.__btnStart.setDisabled(True)
                self.__btnStop.setDisabled(False)
        elif pvname == self.pvStartedAt.pvname:
            self.__leditStartedAt.setText(str(int(value)))
        else:
            raise RunTimeError('run status pvs callback called for unexpected pv')

        logging.info('SequenceDialog._update_run_status() is done')

    def __update_start_config(self, pvname, value, char_value):
        """
        Refer to NOTE02
        """

        logging.info('SequenceDialog.__update_start_config() is running')
    
        if pvname == self.pvSCfgMode.pvname:
            logging.debug('updating radio buttons, value=' + char_value)
            if value == 0:
                self.__rbtn_immediatly.setChecked(True)
            elif value == 1:
                self.__rbtn_modulo.setChecked(True)
            else:
                raise RunTimeError('Invalid mode for start configuration received')
        elif pvname == self.pvSCfgModDivisor.pvname:
            logging.debug('updating ledit divisor, value=' + char_value)
            self.divisor = value
            self.__leditDivisor.setText(char_value)
        elif pvname == self.pvSCfgModOffset.pvname:
            logging.debug('updating ledit offset, value=' + char_value)
            self.offset = value
            self.__leditOffset.setText(char_value)
        else:
            raise RunTimeError('Unexpected call of pv callback function')

        logging.info('SequenceDialog.__update_start_config() is done')

    # NOTE01
    # This function is a callback that is called from pyepics, if the
    # value of a PV changed. It runs in the pyepics thread and emits a
    # signal for the gui event queue thread to handle it.
    #
    # NOTE02
    # This function is a slot. It is called from the gui event queue
    # thread to handle the connected signal.

if __name__ == '__main__':
    
    # setup parser
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            prog='start_cta_gui.sh',
            description='CTA Graphical interface',
            epilog="""Example:
start_cta_gui.sh SFTEST SFTEST-CCTA-TI2
            """
            )
    parser.add_argument(
            'esx', 
            metavar='ESX',
            choices=['ESA', 'ESB', 'ESC', 'ESD', 'ESE', 'ESF', 'SFTEST'],
            help="""Experimental station: ESA, ESB, ESC, ESD, ESE, ESF
Test stand: SFTEST
            """
    )

    parser.add_argument(
            'device', 
            help='Name of device running CTA.'
    )
    parser.add_argument(
            '-l', '--loglevel', 
            metavar='level',
            choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
            default = 'WARNING',
            help="""Specify level for logging
CRITICAL, ERROR, WARNING, INFO, DEBUG
            """
    )
    args = parser.parse_args()

    # setup logging
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=numeric_level, format='%(asctime)s | %(levelname)8s | %(message)s')
    
    # setup application
    app = QApplication(sys.argv)
    app.setStyle("plastique")

    # setup dialog
    dialog = SequenceDialog(args)
    dialog.show()
    
    # run application
    sys.exit(app.exec_())

