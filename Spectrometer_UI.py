# -*- coding: utf-8 -*-

# Author: Matthew Rowley
# Date Created: February 11, 2015

# This program will gather and display spectra from a connected serial device.
# It was written as part of research work at the University of Wisconsin -
# Madison for use in the John C. Wright spectroscopy group.

# This program is licenced under an MIT license. Full licence is at the end of
# this file.

import numpy as np
import sys
import serial
import time
import os
import serial.tools.list_ports
from pyqtgraph import QtCore, QtGui
import pyqtgraph as pg
from scipy.optimize import curve_fit as fit
import csv


class Main_Ui_Window(QtGui.QMainWindow):

    def __init__(self, parent=None):
        # create two GUI state booleans, and data
        self.is_blank = False  # Signal that the next spectrum is a blank
        self.free_running = False
        self.temp = 0.0
        self.humidity = 0.0
        self.pressure = 0.0
        self.center = 0.0
        self.fwhm = 0.0
        # Load config file and create global data objects
        # zero_data is [raw, integration time]
        # active_data is [calibration, corrected, integration time]
        # loaded_data is [calibration, corrected]
        # fit_data is [calibration, corrected]
        self.blank_data = [np.zeros(2048, float), 0]
        self.active_data = [np.array(range(3000, 9000, 2))[:2048]/8000000000.0,
                            np.zeros(2048, float), 5.0]
        self.loaded_data = [np.array(range(3000, 9000, 2))[:2048]/8000000000.0,
                            np.zeros(2048, float)]
        self.fit_data = [np.array(range(3000, 9000, 2))[:2048]/8000000000.0,
                         np.zeros(2048, float)]

        # generate outbound signal and link all signals
        spec_Duino.updated.connect(self.getData)
        sensor_Duino.updated.connect(self.getSensorData)
        spec_Duino.connected.connect(self.checkConnections)
        sensor_Duino.connected.connect(self.checkConnections)
        self.signal = Outbound_Signal()
        self.signal.get_spectrum.connect(spec_Duino.read)
        self.signal.get_sensors.connect(sensor_Duino.read)
        self.signal.set_spec_port.connect(spec_Duino.connectPort)
        self.signal.set_sensor_port.connect(sensor_Duino.connectPort)

        # Create the main UI window with a dark theme
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Tsunami Monitor")
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.Dark, QtCore.Qt.gray)
        palette.setColor(QtGui.QPalette.Light, QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        self.setPalette(palette)
        # Create all the UI objects
        self.main_frame = QtGui.QWidget()
        self.vertical_layout = QtGui.QVBoxLayout(self.main_frame)
        self.vertical_layout.setSizeConstraint(QtGui.QLayout.SetNoConstraint)
        self.parameters_layout = QtGui.QHBoxLayout()
        self.parameters_layout.setMargin(0)
        # Integration Time Label and SpinBox
        self.i_time_label = QtGui.QLabel(self.main_frame)
        self.i_time_label.setToolTip("Set Time to Integrate")
        self.i_time_label.setText("Integration Time (ms):")
        self.parameters_layout.addWidget(self.i_time_label)
        self.i_time_box = QtGui.QSpinBox(self.main_frame)
        self.i_time_box.setWrapping(False)
        self.i_time_box.setButtonSymbols(QtGui.QAbstractSpinBox.UpDownArrows)
        self.i_time_box.setMaximum(10000)
        self.i_time_box.setMinimum(1)
        self.i_time_box.setProperty("value", 5)
        self.i_time_box.setToolTip("Set Time to Integrate")
        self.parameters_layout.addWidget(self.i_time_box)
        # Load Calibration Curve Button
        self.load_cal_button = QtGui.QPushButton(self.main_frame)
        self.load_cal_button.setStyleSheet("background-color: "
                                           "rgb(150, 200, 175);\n")
        self.load_cal_button.setMinimumWidth(170)
        self.load_cal_button.setToolTip("Load a Calibration File to Assign "
                                        "Wavelengths to Pixel Numbers")
        self.load_cal_button.setText("Load Calibration Curve")
        self.parameters_layout.addWidget(self.load_cal_button)
        # Messaging Area
        spacerItemL = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding,
                                        QtGui.QSizePolicy.Minimum)
        self.parameters_layout.addItem(spacerItemL)
        self.message_label = QtGui.QLabel(self.main_frame)
        self.message_label.setToolTip("Messages and Errors are Displayed Here")
        self.updateMessage("Bootup Proceeded Normally")
        self.parameters_layout.addWidget(self.message_label)
        spacerItemR = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding,
                                        QtGui.QSizePolicy.Minimum)
        self.parameters_layout.addItem(spacerItemR)
        # Com Port Labels and ComboBoxes
        self.sensor_port_label = QtGui.QLabel(self.main_frame)
        self.sensor_port_label.setToolTip("Com Port for the Sensor Arduino")
        self.sensor_port_label.setText("Sensor Port:")
        self.parameters_layout.addWidget(self.sensor_port_label)
        self.sensor_port_box = QtGui.QComboBox(self.main_frame)
        self.sensor_port_box.setToolTip("Com Port for the Sensor Arduino")
        self.parameters_layout.addWidget(self.sensor_port_box)
        self.line_9 = QtGui.QFrame(self.main_frame)
        self.line_9.setFrameShape(QtGui.QFrame.VLine)
        self.line_9.setFrameShadow(QtGui.QFrame.Sunken)
        self.parameters_layout.addWidget(self.line_9)
        self.spec_port_label = QtGui.QLabel(self.main_frame)
        self.spec_port_label.setToolTip("Com Port for the Spectrometer "
                                        "Arduino")
        self.spec_port_label.setText("Spectrum Port:")
        self.parameters_layout.addWidget(self.spec_port_label)
        self.spec_port_box = QtGui.QComboBox(self.main_frame)
        self.spec_port_box.setToolTip("Com Port for the Spectrometer Arduino")
        self.findPorts()
        self.parameters_layout.addWidget(self.spec_port_box)
        self.vertical_layout.addLayout(self.parameters_layout)
        self.line_3 = QtGui.QFrame(self.main_frame)
        self.line_3.setFrameShape(QtGui.QFrame.HLine)
        self.line_3.setFrameShadow(QtGui.QFrame.Sunken)
        self.vertical_layout.addWidget(self.line_3)
        self.button_layout = QtGui.QHBoxLayout()
        # Blank Buttons
        self.take_blank_button = QtGui.QPushButton(self.main_frame)
        self.take_blank_button.setToolTip("Acquire a Blank Spectrum to Subract"
                                          " from All Future Spectra")
        self.take_blank_button.setStyleSheet("QPushButton{background-color: "
                                             "rgb(75, 75, 75);\n"
                                             "color: rgb(255, 255, 255);}\n")
        self.take_blank_button.setMaximumWidth(80)
        self.take_blank_button.setText("Take Blank")
        self.button_layout.addWidget(self.take_blank_button)
        self.clear_blank_button = QtGui.QPushButton(self.main_frame)
        self.clear_blank_button.setStyleSheet("background-color: "
                                              "rgb(200, 180, 255);\n")
        self.clear_blank_button.setMaximumWidth(80)
        self.clear_blank_button.setText("Clear Blank")
        self.clear_blank_button.setToolTip("Clear the Currently Stored Blank")
        self.button_layout.addWidget(self.clear_blank_button)
        self.line_1 = QtGui.QFrame(self.main_frame)
        self.line_1.setFrameShape(QtGui.QFrame.VLine)
        self.line_1.setFrameShadow(QtGui.QFrame.Sunken)
        self.button_layout.addWidget(self.line_1)
        # Acquire Buttons
        self.take_snapshot_button = QtGui.QPushButton(self.main_frame)
        self.take_snapshot_button.setStyleSheet("background-color: "
                                                "rgb(255, 180, 100);\n")
        self.take_snapshot_button.setMaximumWidth(200)
        self.take_snapshot_button.setText("Take Snapshot")
        self.take_snapshot_button.setToolTip("Acquire One Spectrum")
        self.button_layout.addWidget(self.take_snapshot_button)
        self.free_running_button = QtGui.QCheckBox(self.main_frame)
        self.free_running_button.setCheckable(True)
        self.free_running_button.setMaximumWidth(18)
        self.free_running_button.setToolTip("Acquire New Spectra as Quickly "
                                            "as Possible")
        self.button_layout.addWidget(self.free_running_button)
        # Note that the dark color palette doesn't seem to get the checkbox
        # text to be white, so we make a label instead
        self.free_running_label = QtGui.QLabel(self.main_frame)
        self.free_running_label.setText("Free Running Mode")
        self.free_running_label.setToolTip("Acquire New Spectra as Quickly "
                                           "as Possible")
        self.free_running_label.setMaximumWidth(115)
        self.button_layout.addWidget(self.free_running_label)
        spacerItem1 = QtGui.QSpacerItem(400, 520, QtGui.QSizePolicy.Preferred,
                                        QtGui.QSizePolicy.Preferred)
        self.button_layout.addItem(spacerItem1)
        # Save/load Buttons
        self.save_button = QtGui.QPushButton(self.main_frame)
        self.save_button.setStyleSheet("background-color: rgb(255, 130, 130);")
        self.save_button.setMaximumWidth(200)
        self.save_button.setToolTip("Save the Current Spectrum to a File")
        self.save_button.setText("Save Spectrum")
        self.button_layout.addWidget(self.save_button)
        self.load_button = QtGui.QPushButton(self.main_frame)
        self.load_button.setStyleSheet("background-color: rgb(90, 250, 90);")
        self.load_button.setMaximumWidth(200)
        self.load_button.setToolTip("Load a Saved Spectrum")
        self.load_button.setText("Load Spectrum")
        self.button_layout.addWidget(self.load_button)
        self.vertical_layout.addLayout(self.button_layout)
        self.line = QtGui.QFrame(self.main_frame)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.vertical_layout.addWidget(self.line)
        self.fit_values_layout = QtGui.QHBoxLayout()
        self.curser_label = QtGui.QLabel(self.main_frame)
        self.curser_label.setToolTip("Value at the Blue Vertical Curser")
        self.curser_label.setText("Curser Position:")
        self.fit_values_layout.addWidget(self.curser_label)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding,
                                        QtGui.QSizePolicy.Minimum)
        self.fit_values_layout.addItem(spacerItem2)
        self.center_label = QtGui.QLabel(self.main_frame)
        self.center_label.setText("Center:  ")
        self.center_label.setToolTip("Center of Best Gaussian Fit")
        self.fit_values_layout.addWidget(self.center_label)
        self.line_4 = QtGui.QFrame(self.main_frame)
        self.line_4.setFrameShape(QtGui.QFrame.VLine)
        self.line_4.setFrameShadow(QtGui.QFrame.Sunken)
        self.fit_values_layout.addWidget(self.line_4)
        self.fwhm_label = QtGui.QLabel(self.main_frame)
        self.fwhm_label.setText("FWHM:  ")
        self.fwhm_label.setToolTip("FWHM of Best Gaussian Fit")
        self.fit_values_layout.addWidget(self.fwhm_label)
        self.line_5 = QtGui.QFrame(self.main_frame)
        self.line_5.setFrameShape(QtGui.QFrame.VLine)
        self.line_5.setFrameShadow(QtGui.QFrame.Sunken)
        self.fit_values_layout.addWidget(self.line_5)
        self.temp_label = QtGui.QLabel(self.main_frame)
        self.temp_label.setText("Temp:  ")
        self.temp_label.setToolTip("Current Ambient Temperature")
        self.fit_values_layout.addWidget(self.temp_label)
        self.line_6 = QtGui.QFrame(self.main_frame)
        self.line_6.setFrameShape(QtGui.QFrame.VLine)
        self.line_6.setFrameShadow(QtGui.QFrame.Sunken)
        self.fit_values_layout.addWidget(self.line_6)
        self.humidity_label = QtGui.QLabel(self.main_frame)
        self.humidity_label.setText("Humidity:  ")
        self.humidity_label.setToolTip("Current Ambient Humidity")
        self.fit_values_layout.addWidget(self.humidity_label)
        self.line_7 = QtGui.QFrame(self.main_frame)
        self.line_7.setFrameShape(QtGui.QFrame.VLine)
        self.line_7.setFrameShadow(QtGui.QFrame.Sunken)
        self.fit_values_layout.addWidget(self.line_7)
        self.pressure_label = QtGui.QLabel(self.main_frame)
        self.pressure_label.setText("Pressure:  ")
        self.pressure_label.setToolTip("Current Ambient Pressure")
        self.fit_values_layout.addWidget(self.pressure_label)
        self.vertical_layout.addLayout(self.fit_values_layout)
        # The plot widget
        self.plot_object = pg.PlotWidget()
        self.plot_object.getPlotItem().setMouseEnabled(False, False)
        self.plot_object.setLabel('bottom', 'Wavelength', units='m')
        self.plot_object.setLabel('left', 'Raw')
        self.plot_object.setLimits(xMin=500.0 * 10**-9,
                                   xMax=1000 * 10**-9)
        # Create and add things to the plot widget
        self.curser = pg.InfiniteLine(pos=0.00000080000, angle=90,
                                      pen=(75, 100), movable=True)
        self.plot_object.addItem(self.curser)
        self.loaded_curve = pg.PlotCurveItem(pen=(35, 100))
        self.plot_object.addItem(self.loaded_curve)
        self.updateLoadedData()
        self.loaded_point = pg.CurvePoint(self.loaded_curve)
        self.plot_object.addItem(self.loaded_point)
        self.loaded_arrow = pg.ArrowItem(angle=55, pen=(39, 100),
                                         brush=(35, 100), tailLen=20)
        self.loaded_arrow.setParentItem(self.loaded_point)
        self.loaded_text = pg.TextItem("Loaded Curve:", color=(50, 250, 50),
                                       anchor=(0.05, -1.25))
        self.loaded_text.setParentItem(self.loaded_point)
        self.loaded_point.setPos(0.20)
        self.active_curve = pg.PlotCurveItem(pen=(0, 100))
        self.plot_object.addItem(self.active_curve)
        self.fit_curve = pg.PlotCurveItem(pen=(10, 100))
        self.plot_object.addItem(self.fit_curve)

        self.vertical_layout.addWidget(self.plot_object)
        self.setCentralWidget(self.main_frame)
        # connect all the ui widgets to functions
        self.curser.sigPositionChanged.connect(self.curserMoved)
        self.i_time_box.valueChanged.connect(self.setIntegrationT)
        self.load_cal_button.clicked.connect(self.loadCalibration)
        self.sensor_port_box.currentIndexChanged.connect(self.selectSensorPort)
        self.spec_port_box.currentIndexChanged.connect(self.selectSpecPort)
        self.take_blank_button.clicked.connect(self.takeBlank)
        self.clear_blank_button.clicked.connect(self.clearBlank)
        self.take_snapshot_button.clicked.connect(self.takeSnapshot)
        self.free_running_button.toggled.connect(self.setFreeRunning)
        self.save_button.clicked.connect(self.saveCurve)
        self.load_button.clicked.connect(self.loadCurve)
        # Start collecting sensor data and load the config
        self.signal.get_sensors.emit()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.signal.get_sensors.emit)
        self.timer.start(10000)  # update sensor data every 10s
        self.loadConfig()

    # These methods are called as part of startup
    def loadConfig(self):  # Loads the previously used settings
        try:
            with open(".spec.config", "r") as config_file:
                lines = config_file.readlines()
                # Set the port combo boxes and attempt to connect
                self.sensor_port_box.setCurrentIndex(self.sensor_port_box.
                                                     findText(lines[1][:-1]))
                self.spec_port_box.setCurrentIndex(self.spec_port_box.
                                                   findText(lines[3][:-1]))
                self.importCalibration(lines[5][:-1])
                self.importCurve(lines[7][:-1])
                self.blank_data[1] = int(lines[9])
                self.i_time_box.setValue(int(lines[9]))
                self.setIntegrationT(verbose=False)
                for index, value in enumerate(lines[11:]):
                    self.blank_data[0][index] = float(value)
        except OSError as e:
            self.updateMessage("**Filename Error - spec.config File Not "
                               "Properly Imported**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - spec.config File Not "
                               "Properly Imported**\n" + str(e)[:60])
            print(e)

    def findPorts(self):
        self.ports = serial.tools.list_ports.comports()
        for index, comport in enumerate(self.ports[::-1]):
            self.sensor_port_box.addItem(comport[0])
            self.spec_port_box.addItem(comport[0])
        if len(self.ports) == 0:
            self.updateMessage("**No Available Com Ports Detected**")

    # Close the arduino threads gracefully when the window closes
    def closeEvent(self, evt):
        if self.free_running:
            self.free_running_button.setChecked(False)
        spec_Duino.closePort()
        sensor_Duino.closePort()
        spec_thread.quit()
        sensor_thread.quit()
        while(not spec_thread.isFinished() or not sensor_thread.isFinished()):
            time.sleep(1)
        QtGui.QMainWindow.closeEvent(self, evt)

    # These methods are for interacting with the graph
    def curserMoved(self):
        xposition = self.curser.value()
        if xposition < 1:
            self.curser_label.setText("Curser Position:  {0:.2f} nm"
                                      .format(xposition * 10**9))
        else:
            self.curser_label.setText("Curser Position:  Pixel No. {}"
                                      .format(int(xposition)))

    def mousePressEvent(self, evt):
        position = evt.pos()
        if self.plot_object.frameGeometry().contains(position):
            position.setX(position.x() - self.plot_object.frameGeometry().x())
            view_box = self.plot_object.getPlotItem().getViewBox()
            curser_pos = view_box.mapSceneToView(position)
            view_range = self.plot_object.getPlotItem().viewRange()[0]
            if curser_pos.x() > view_range[0] and \
               curser_pos.x() < view_range[1]:
                self.curser.setValue(curser_pos)

    # Button press methods
    def setIntegrationT(self, verbose=True):
        i_Time.write(self.i_time_box.value())
        message = self.message_label.text()
        if verbose:
            message = ("Integration time set to {} ms - {}"
                       .format(self.i_time_box.value(),
                               time.strftime("%Y-%m-%d %H:%M:%S")))
        if self.i_time_box.value() != self.blank_data[1] and \
           self.blank_data[1] != 0:
            message = (message + "\n*Integration Time is Not the Same as That "
                       "Used for the Blank ({} ms) - Consider Taking a New "
                       "Blank*".format(self.blank_data[1]))
        self.updateMessage(message)

    def loadCalibration(self):
        was_free_running = False
        if(self.free_running):
            self.free_running_button.setChecked(False)
            was_free_running = True
        load_path = (QtGui.QFileDialog.getOpenFileName(
                     self, "Select a Calibration Curve File", "",
                     "Calibration Files (*.cal);;All Files (*.*)"))
        if len(load_path) == 0:
            self.updateMessage("**Calibration Loading Cancelled - {}**"
                               .format(time.strftime("%Y-%m-%d %H:%M:%S")))
            if was_free_running:
                self.free_running_button.setChecked(True)
            return
        self.importCalibration(load_path)
        self.calToConfig(load_path)
        if was_free_running:
            self.free_running_button.setChecked(True)

    def selectSensorPort(self):
        spec_index = self.spec_port_box.currentIndex()
        sensor_index = self.sensor_port_box.currentIndex()
        if sensor_index != spec_index:
            sensor_Port.write(self.sensor_port_box.currentText())
            self.signal.set_sensor_port.emit()
        else:
            self.updateMessage("**Please Select Different Com Ports for "
                               "Sensor and Spectrometer**")

    def selectSpecPort(self):
        spec_index = self.spec_port_box.currentIndex()
        sensor_index = self.sensor_port_box.currentIndex()
        if sensor_index != spec_index:
            spec_Port.write(self.spec_port_box.currentText())
            self.signal.set_spec_port.emit()
        else:
            self.updateMessage("**Please Select Different Com Ports for "
                               "Sensor and Spectrometer**")

    def takeBlank(self):
        self.is_blank = True
        self.signal.get_spectrum.emit()

    def clearBlank(self):
        self.applyBlank([np.zeros(2048, float), 0])
        self.updateActiveData()
        self.findFit()
        self.updateMessage("Blank Cleared - {}"
                           .format(time.strftime("%Y-%m-%d %H:%M:%S")))

    def takeSnapshot(self):
        if(self.free_running):
            self.free_running_button.setChecked(False)
        self.signal.get_spectrum.emit()
        self.updateMessage("Snapshot Initiated - {}"
                           .format(time.strftime("%Y-%m-%d %H:%M:%S")))

    def setFreeRunning(self):
        self.free_running = self.free_running_button.isChecked()
        if self.free_running:
            self.updateMessage("Free-Running Mode Enabled - {}"
                               .format(time.strftime("%Y-%m-%d %H:%M:%S")))
            self.signal.get_spectrum.emit()
        else:
            self.updateMessage("Free-Running Mode Disabled - {}"
                               .format(time.strftime("%Y-%m-%d %H:%M:%S")))

    def saveCurve(self):
        was_free_running = False
        if(self.free_running):
            self.free_running_button.setChecked(False)
            was_free_running = True
        default_path = time.strftime("%Y-%m-%d_%H:%M:%S")
        save_path = (QtGui.QFileDialog.getSaveFileName(
                     self, "Save File As", default_path,
                     "Spectrum Files (*.csv);;All Files (*.*)"))
        if len(save_path) == 0:
            self.updateMessage("**Save Spectrum Cancelled - {}**"
                               .format(time.strftime("%Y-%m-%d %H:%M:%S")))
            if was_free_running:
                self.free_running_button.setChecked(True)
            return
        if save_path[-4:] != ".csv":
            save_path = save_path + ".csv"
        try:
            with open(save_path, 'wt') as save_file:
                header = self.generateHeader()
                save_file.write(header)
                writer = csv.writer(save_file, dialect="excel-tab")
                cal = self.active_data[0]
                dat = self.active_data[1]
                blank = self.blank_data[0]
                for rownum in range(len(cal)):
                    row = [cal[rownum], dat[rownum], blank[rownum]]
                    writer.writerow(row)
            self.updateMessage("Spectrum Saved - {}"
                               .format(time.strftime("%Y-%m-%d %H:%M:%S")))
        except OSError as e:
            self.updateMessage("**Filename Error - Spectrum May Have Not "
                               "Saved Properly**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - Spectrum May Have Not "
                               "Saved Properly**\n" + str(e)[:60])
            print(e)
        if was_free_running:
            self.free_running_button.setChecked(True)

    def loadCurve(self):
        was_free_running = False
        if(self.free_running):
            self.free_running_button.setChecked(False)
            was_free_running = True
        load_path = (QtGui.QFileDialog.getOpenFileName(
                     self, "Select a Spectrum to Load", "",
                     "Spectrum Files (*.csv);;All Files (*.*)"))
        if len(load_path) == 0:
            self.updateMessage("**Spectrum Loading Cancelled - {}**"
                               .format(time.strftime("%Y-%m-%d %H:%M:%S")))
            if was_free_running:
                self.free_running_button.setChecked(True)
            return
        self.importCurve(load_path)
        self.loadToConfig(load_path)
        if was_free_running:
            self.free_running_button.setChecked(True)

    # These functions load data from files
    def importCalibration(self, load_path):
        try:
            with open(load_path, "r") as load_file:
                reader = csv.reader(load_file)
                new_calibration = np.zeros(2048, float)
                starting_row = 1
                for index, row in enumerate(reader):
                    if index >= starting_row:
                        new_calibration[index - starting_row] = float(row[1])
                self.active_data[0] = new_calibration
                self.fit_data[0] = new_calibration
                self.curser.setValue(new_calibration[1024])
                self.findFit()
            # A calibration file with "Dummy" in the name gives pixel number
            # (from 0 to 2047). To use it we must allow the plot to expand
            if "Dummy" in load_path:
                self.plot_object.setLimits(xMin=-2, xMax=2050)
                self.plot_object.setLabel('bottom', 'Pixel', units="")
            # But normally, it is better to constrain zooming on the plot
            else:
                self.plot_object.setLimits(xMin=500.0 * 10**-9,
                                           xMax=1000 * 10**-9)
                self.plot_object.setLabel('bottom', 'Wavelength', units='m')
            self.updateActiveData()
            self.updateMessage("Calibration Loaded Successfully")
        except OSError as e:
            self.updateMessage("**Filename Error - Calibration May Have Not "
                               "Loaded Properly**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - Calibration May Have Not "
                               "Loaded Properly**\n" + str(e)[:60])
            print(e)

    def importCurve(self, load_path):
        try:
            with open(load_path, "r") as load_file:
                reader = csv.reader(load_file, dialect='excel-tab')
                new_calibration = np.zeros(2048, float)
                new_data = np.zeros(2048, float)
                starting_row = 15
                for index, row in enumerate(reader):
                    if index >= starting_row:
                        new_calibration[index - starting_row] = float(row[0])
                        new_data[index - starting_row] = float(row[1])
                self.loaded_data[0] = new_calibration
                self.loaded_data[1] = new_data
            self.updateLoadedData()
            self.updateMessage("Spectrum Loaded - {}"
                               .format(time.strftime("%Y-%m-%d %H:%M:%S")))
            # Add a useful message about the filename of the loaded curve
            self.loaded_point.setPos(0.20)
            filename = os.path.basename(load_path)
            self.loaded_text.setText("Loaded Curve: " + filename,
                                     color=(50, 250, 50))
        except OSError as e:
            self.updateMessage("**Filename Error - Spectrum May Have Not "
                               "Loaded Properly**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - Spectrum May Have Not "
                               "Loaded Properly**\n" + str(e)[:60])
            print(e)

    # These functions write to the .spec.config file when settings are changed
    def blankToConfig(self):
        # Try saving the blank data to the spec.config file
        try:
            with open(".spec.config", "r") as config_file:
                lines = config_file.readlines()
            lines[8] = "Integration Time at Last Blank Taken:\n"
            lines[9] = str(self.blank_data[1]) + "\n"
            lines[10] = "Last Blank Taken:"
            for index, value in enumerate(self.blank_data[0]):
                lines[11 + index] = "\n" + str(value)
            with open(".spec.config", "wt") as config_file:
                config_file.writelines(lines)
        except OSError as e:
            self.updateMessage("**Filename Error - spec.config File Not "
                               "Properly Written**\n" + str(e)[:60])
        except Exception as e:
            self.updateMessage("**Unknown Error - spec.config File Not "
                               "Properly Written**\n" + str(e)[:60])
            print(e)

    def loadToConfig(self, load_path):
        # Try saving the loaded filename to the spec.config file
        try:
            with open(".spec.config", "r") as config_file:
                lines = config_file.readlines()
            lines[6] = "Spectrum File Last Loaded:\n"
            lines[7] = str(load_path) + "\n"
            with open(".spec.config", "wt") as config_file:
                config_file.writelines(lines)
        except OSError as e:
            self.updateMessage("**Filename Error - spec.config File Not "
                               "Properly Written**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - spec.config File Not "
                               "Properly Written**\n" + str(e)[:60])
            print(e)

    def calToConfig(self, load_path):
        # Try saving the calibration filename to the spec.config file
        try:
            with open(".spec.config", "r") as config_file:
                lines = config_file.readlines()
            lines[4] = "Calibration File Last Used:\n"
            lines[5] = str(load_path) + "\n"
            with open(".spec.config", "wt") as config_file:
                config_file.writelines(lines)
        except OSError as e:
            self.updateMessage("**Filename Error - spec.config File Not "
                               "Properly Written**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - spec.config File Not "
                               "Properly Written**\n" + str(e)[:60])
            print(e)

    def portsToConfig(self):
        # Try saving the com ports to the spec.config file
        try:
            with open(".spec.config", "r") as config_file:
                lines = config_file.readlines()
            lines[0] = "Sensor Port Last Used:\n"
            lines[1] = self.sensor_port_box.currentText() + "\n"
            lines[2] = "Spec Port Last Used:\n"
            lines[3] = self.spec_port_box.currentText() + "\n"
            with open(".spec.config", "wt") as config_file:
                config_file.writelines(lines)
        except OSError as e:
            self.updateMessage("**Filename Error - spec.config File Not "
                               "Properly Written**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - spec.config File Not "
                               "Properly Written**\n" + str(e)[:60])
            print(e)

    # These functions are called when the Arduinos send signals
    def getData(self):  # A signal says there is new data in spectrum object
        if self.free_running:
            # Start getting the next spectrum right away
            self.signal.get_spectrum.emit()
        if self.is_blank:  # The new data must be from a blank
            self.applyBlank(spectrum.read())
            self.updateMessage("Blank Taken - {}"
                               .format(time.strftime("%Y-%m-%d %H:%M:%S")))
            self.is_blank = False
        else:
            self.active_data[1:3] = spectrum.read()
        self.active_data[1] = self.active_data[1] - self.blank_data[0]
        self.updateActiveData()
        self.findFit()

    # A signal says there is new sensor data in the sensor_Data object
    def getSensorData(self):
        self.temp, self.humidity, self.pressure = sensor_Data.read()
        # This is necessary to properly handle the degree glyph in python 2
        try:
            self.temp_label.setText(QtCore.QString
                                    .fromUtf8("{0:.2f} °C".format(self.temp)))
        except Exception:
            self.temp_label.setText("Temp:  {0:.2f} °C".format(self.temp))
        self.humidity_label.setText("Humidity:  {0:.2f} %"
                                    .format(self.humidity))
        self.pressure_label.setText("Pressure:  {0:.2f} pa"
                                    .format(self.pressure))

    def checkConnections(self):
        status = port_Status.read()
        if status[0]:
            message = "Sensor Arduino Connected Properly\n"
        else:
            message = "**Warning! Sensor Arduino Could Not Connect - Dummy "\
                      "Data is Being Generated**\n"
        if status[1]:
            message += "Spectrum Arduino Connected Properly"
        else:
            message += "**Warning! Spetrum Arduino Could Not Connect - Dummy "\
                       "Data is Being Generated**"
        self.updateMessage(message)
        if status[0] and status[1]:  # only save successfull settings
            self.portsToConfig()

    # Some extra functions for dealing with data
    def findFit(self):
        amplitude_guess = np.amax(self.active_data[1])
        center_guess = self.active_data[0][1024]
        fwhm_guess = 80 * 10.0**-9.0
        offset_guess = 2.5
        guesses = [amplitude_guess, center_guess, fwhm_guess, offset_guess]
        fit_vals, cov = fit(gaussian, self.active_data[0],
                            self.active_data[1], p0=guesses)
        self.fit_data[1] = gaussian(self.fit_data[0], fit_vals[0], fit_vals[1],
                                    fit_vals[2], fit_vals[3])
        self.center = fit_vals[1]
        self.fwhm = fit_vals[2]
        self.fit_curve.setData(self.fit_data[0], self.fit_data[1])
        self.center_label.setText("Center:  {0:.2f} nm"
                                  .format(self.center * 10**9))
        self.fwhm_label.setText("FWHM:  {0:.2f} nm".format(self.fwhm * 10**9))

    def applyBlank(self, new_blank):
        # First undo the old blank on the currently active data
        old_blank = self.blank_data
        self.active_data[1] = self.active_data[1] + old_blank[0]
        self.blank_data = new_blank
        self.blankToConfig()

    # Some functions that update the ui
    def updateActiveData(self):
        self.active_curve.setData(self.active_data[0], self.active_data[1])

    def updateLoadedData(self):
        self.loaded_curve.setData(self.loaded_data[0], self.loaded_data[1])

    def updateMessage(self, message):
        self.message_label.setText(message)

    def generateHeader(self):
        header = ("This spectrum was collected on:\t" +
                  time.strftime("%Y-%m-%d\t%H:%M:%S\n"))
        header += "Integration Time:\t{}\tms\n".format(self.active_data[2])
        header += "------------------------\n"
        header += "Environmental Parameters\n"
        header += "------------------------\n"
        header += "Temp:\t{0:.2f}\tdegrees C\n".format(self.temp)
        header += "Humidity:\t{0:.2f}\t%\n".format(self.humidity)
        header += "Pressure:\t{0:.2f}\tpa\n".format(self.pressure)
        header += "--------------\n"
        header += "Fit Parameters\n"
        header += "--------------\n"
        header += "Center:\t{0:.3e}\tm\n".format(self.center)
        header += "FWHM:\t{0:.2e}\tm\n\n".format(self.fwhm)
        header += "Wavelength (m)\tCorrected Signal\tApplied Blank\n"
        return header


# These mutex objects communicate between asynchronous arduino and gui threads
class Spectrum(QtCore.QMutex):

    def __init__(self):
        QtCore.QMutex.__init__(self)
        self.value = [np.zeros(2048, float), 5]

    def read(self):
        return self.value

    def write(self, new_value):
        self.lock()
        self.value = new_value
        self.unlock()


class Sensor_Data(QtCore.QMutex):

    def __init__(self):
        QtCore.QMutex.__init__(self)
        self.value = [0.0, 0.0, 0.0]  # temp, humidity, pressure

    def read(self):
        return self.value

    def write(self, new_value):
        self.lock()
        self.value = new_value
        self.unlock()


class I_Time(QtCore.QMutex):
    def __init__(self):
        QtCore.QMutex.__init__(self)
        self.value = 5

    def read(self):
        return self.value

    def write(self, new_value):
        self.lock()
        self.value = new_value
        self.unlock()


class Com_Port(QtCore.QMutex):
    def __init__(self):
        QtCore.QMutex.__init__(self)
        self.value = None

    def read(self):
        return self.value

    def write(self, new_value):
        self.lock()
        self.value = new_value
        self.unlock()


class Port_Status(QtCore.QMutex):
    def __init__(self):
        QtCore.QMutex.__init__(self)
        self.value = [False, False]  # Connection status of sensor, spec ports

    def read(self):
        return self.value

    def write(self, new_value):
        self.lock()
        self.value = new_value
        self.unlock()


# These classes handle the communication between arduinos
class Outbound_Signal(QtCore.QObject):
    get_spectrum = QtCore.pyqtSignal()
    get_sensors = QtCore.pyqtSignal()
    set_spec_port = QtCore.pyqtSignal()
    set_sensor_port = QtCore.pyqtSignal()


class Sensor_Duino(QtCore.QObject):
    updated = QtCore.pyqtSignal()
    connected = QtCore.pyqtSignal()
    port = None
    valid_connection = False

    def read(self):
        if not self.valid_connection:  # Generate dummy data
            data = np.random.uniform(0, 12, 3)
        else:  # Get data from the Arduino
            self.port.write('r')
            raw_vals = self.port.readline()
            data = np.fromstring(raw_vals, dtype=float, sep=',')
        sensor_Data.write(data)
        self.updated.emit()

    def connectPort(self):
        status = port_Status.read()
        self.closePort()
        try:
            self.port = serial.Serial(port=sensor_Port.read(), baudrate=9600,
                                      timeout=2)
            print("Connecting to the Sensor_Duino on port " +
                  str(sensor_Port.read()))
            status[0] = True
            self.valid_connection = True
        except Exception as e:
            print(e)
            status[0] = False
            self.valid_connection = False
        port_Status.write(status)
        self.connected.emit()

    def closePort(self):
        print("Closing Sensor port if open")
        try:
            self.port.close()
        except Exception as e:
            print(e)


class Spec_Duino(QtCore.QObject):
    updated = QtCore.pyqtSignal()
    connected = QtCore.pyqtSignal()
    port = None
    valid_connection = False

    def read(self):
        i_time = str(i_Time.read()) + " "
        if not self.valid_connection:
            # this generates a random gaussian dummy spectrum
            amp = 3000. + np.random.random() * 1000
            center = 875. + np.random.random() * 300
            fwhm = 300. + np.random.random() * 100
            offset = np.random.random() * 4
            data = np.random.uniform(0, 100, 2048)
            data = data + gaussian(np.arange(2048), amp, center, fwhm, offset)
        else:  # Get real data from the arduino
            data = np.zeros(2048)
            self.port.write(i_time.encode())
            stream = self.port.read(4096)
            for i in range(2048):
                data[i] = stream[2*i] << 8 | stream[2*i+1]
        spectrum.write([data, i_time])
        self.updated.emit()

    def connectPort(self):
        status = port_Status.read()
        self.closePort()
        try:
            self.port = serial.Serial(port=spec_Port.read(), baudrate=115200,
                                      timeout=2)
            print("Connecting to the Spec_Duino on port " +
                  str(spec_Port.read()))
            response = str(self.port.readline())
            if "Spec" not in response:
                print('Response on the Serial Port:{}'.format(response))
                #raise ConnectionError("Spec Arduino may not be running proper "
                #                      "firmware")
            # Sometimes an errant extra "Spec" appears in the input buffer
            self.port.readline()  # This clears "Spec" or waits 2s to timeout
            status[1] = True
            self.valid_connection = True
        except Exception as e:
            print(e)
            status[1] = False
            self.valid_connection = False
        port_Status.write(status)
        self.connected.emit()

    def closePort(self):
        print("Closing Spec port if open")
        try:
            self.port.close()
        except Exception as e:
            print(e)


# Define a lambda function for use in fitting
def gaussian(x, amp, center, fwhm, offset):
    return amp * np.exp(-(x-center)**2/(2*fwhm**2)) + offset


def main():
    # Set the cwd to the Data folder to make it easy in the file dialogs
    try:  # First try using the filepath of the Spectrometer_Ui.py file
        file_path = os.path.abspath(__file__)
        folder_path = os.path.dirname(file_path)
        data_path = os.path.join(folder_path, "Data")
        os.chdir(data_path)
    except:  # Next try using the cwd
        folder_path = os.getcwd()
        data_path = os.path.join(folder_path, "Data")
        try:
            os.chdir(data_path)
        except:
            print("**Current Working Directory is NOT the Data Directory**")
    global MainWindow
    MainWindow = Main_Ui_Window()
    MainWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
    MainWindow.showMaximized()
    return MainWindow

# Instantiate the application
app = QtGui.QApplication(sys.argv)

# Generate the mutex objects
spectrum = Spectrum()
sensor_Data = Sensor_Data()
i_Time = I_Time()
spec_Port = Com_Port()
sensor_Port = Com_Port()
port_Status = Port_Status()

# Generate the Arduinos and start them in their own threads
spec_Duino = Spec_Duino()
spec_thread = QtCore.QThread()
spec_Duino.moveToThread(spec_thread)
spec_thread.start()
sensor_Duino = Sensor_Duino()
sensor_thread = QtCore.QThread()
sensor_Duino.moveToThread(sensor_thread)
sensor_thread.start()

# Create the GUI and start the application
main_form = main()
app.exec_()

# ToDo: Implement integration time in bytes if possible

# The MIT License (MIT)
#
# Copyright (c) 2015 Matthew B. Rowley
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
