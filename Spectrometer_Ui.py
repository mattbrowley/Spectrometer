# -*- coding: utf-8 -*-

# Author: Matthew Rowley
# Date Created: February 11, 2015

import numpy as np
import sys, serial, time, os
import serial.tools.list_ports
from pyqtgraph import QtCore, QtGui
import pyqtgraph as pg
from scipy.optimize import curve_fit as fit
import csv

class Main_Ui_Window(QtGui.QMainWindow):
    def __init__(self, parent = None):
        # create two GUI state booleans, and data
        self.is_blank = False # This signals that the next spectrum should be a blank
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
        self.active_data = [np.array(range(3000,9000,2))[:2048]/8000000000.0,
                            np.zeros(2048, float), 5.0]
        self.loaded_data = [np.array(range(3000,9000,2))[:2048]/8000000000.0,
                            np.zeros(2048, float)]
        self.fit_data = [np.array(range(3000,9000,2))[:2048]/8000000000.0,
                         np.zeros(2048, float)]

        #generate outbound signal and link all signals
        spec_Duino.updated.connect(self.getData)
        sensor_Duino.updated.connect(self.getSensorData)
        self.signal = Outbound_Signal()
        self.signal.get_spectrum.connect(spec_Duino.read)
        self.signal.get_sensors.connect(sensor_Duino.read)

        # Create the main UI window
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Tsunami Monitor")
        # Create all the UI objects
        self.main_frame = QtGui.QWidget()
        self.main_frame.setObjectName("main_frame")
        self.vertical_layout = QtGui.QVBoxLayout(self.main_frame)
        self.vertical_layout.setSizeConstraint(QtGui.QLayout.SetNoConstraint)
        self.vertical_layout.setObjectName("vertical_layout")
        self.parameters_layout = QtGui.QHBoxLayout()
        self.parameters_layout.setMargin(0)
        self.parameters_layout.setObjectName("parameters_layout")
        # Integration Time Label and SpinBox
        self.i_time_label = QtGui.QLabel(self.main_frame)
        self.i_time_label.setObjectName("i_time_label")
        self.i_time_label.setText("Integration Time (ms):")
        self.parameters_layout.addWidget(self.i_time_label)
        self.i_time_box = QtGui.QSpinBox(self.main_frame)
        self.i_time_box.setWrapping(False)
        self.i_time_box.setButtonSymbols(QtGui.QAbstractSpinBox.UpDownArrows)
        self.i_time_box.setMaximum(10000)
        self.i_time_box.setMinimum(1)
        self.i_time_box.setProperty("value", 5)
        self.i_time_box.setObjectName("i_time_box")
        self.parameters_layout.addWidget(self.i_time_box)
        # Load Calibration Curve Button
        self.load_cal_button = QtGui.QPushButton(self.main_frame)
        self.load_cal_button.setStyleSheet("background-color: rgb(150, 200, 175);\n")
        self.load_cal_button.setMinimumWidth(170)
        self.load_cal_button.setObjectName("load_cal_button")
        self.load_cal_button.setText("Load Calibration Curve")
        self.parameters_layout.addWidget(self.load_cal_button)
        # Messaging Area
        spacerItemL = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.parameters_layout.addItem(spacerItemL)
        self.message_label = QtGui.QLabel(self.main_frame)
        self.message_label.setObjectName("message_label")
        self.updateMessage("Bootup Proceeded Normally")
        self.parameters_layout.addWidget(self.message_label)
        spacerItemR = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.parameters_layout.addItem(spacerItemR)
        # Com Port Labels and ComboBoxes
        self.sensor_port_label = QtGui.QLabel(self.main_frame)
        self.sensor_port_label.setObjectName("sensor_port_label")
        self.sensor_port_label.setText("Sensor Port:")
        self.parameters_layout.addWidget(self.sensor_port_label)
        self.sensor_port_box = QtGui.QComboBox(self.main_frame)
        self.sensor_port_box.setObjectName("sensor_port_box")
        self.parameters_layout.addWidget(self.sensor_port_box)
        self.line_9 = QtGui.QFrame(self.main_frame)
        self.line_9.setFrameShape(QtGui.QFrame.VLine)
        self.line_9.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_9.setObjectName("line_9")
        self.parameters_layout.addWidget(self.line_9)
        self.com_port_label = QtGui.QLabel(self.main_frame)
        self.com_port_label.setObjectName("com_port_label")
        self.com_port_label.setText("Com Port:")
        self.parameters_layout.addWidget(self.com_port_label)
        self.com_port_box = QtGui.QComboBox(self.main_frame)
        self.com_port_box.setObjectName("com_port_box")
        self.findPorts()
        self.parameters_layout.addWidget(self.com_port_box)
        self.vertical_layout.addLayout(self.parameters_layout)
        self.line_3 = QtGui.QFrame(self.main_frame)
        self.line_3.setFrameShape(QtGui.QFrame.HLine)
        self.line_3.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.vertical_layout.addWidget(self.line_3)
        self.button_layout = QtGui.QHBoxLayout()
        self.button_layout.setObjectName("button_layout")
        # Blank Buttons
        self.take_blank_button = QtGui.QPushButton(self.main_frame)
        self.take_blank_button.setToolTip("Acquire a Blank Spectrum to Subract from All Future Spectra")
        self.take_blank_button.setStyleSheet("QPushButton{background-color: rgb(75, 75, 75);\n"
                                             "color: rgb(255, 255, 255);}\n")
        self.take_blank_button.setMaximumWidth(80)
        self.take_blank_button.setObjectName("take_blank_button")
        self.take_blank_button.setText("Take Blank")
        self.button_layout.addWidget(self.take_blank_button)
        self.clear_blank_button = QtGui.QPushButton(self.main_frame)
        self.clear_blank_button.setStyleSheet("background-color: rgb(200, 180, 255);\n")
        self.clear_blank_button.setMaximumWidth(80)
        self.clear_blank_button.setObjectName("take_blank_button")
        self.clear_blank_button.setText("Clear Blank")
        self.clear_blank_button.setToolTip("Clear the Currently Stored Blank")
        self.button_layout.addWidget(self.clear_blank_button)
        self.line_1 = QtGui.QFrame(self.main_frame)
        self.line_1.setFrameShape(QtGui.QFrame.VLine)
        self.line_1.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_1.setObjectName("line_1")
        self.button_layout.addWidget(self.line_1)
        # Acquire Buttons
        self.take_snapshot_button = QtGui.QPushButton(self.main_frame)
        self.take_snapshot_button.setStyleSheet("background-color: rgb(255, 180, 100);\n")
        self.take_snapshot_button.setMaximumWidth(200)
        self.take_snapshot_button.setObjectName("take_snapshot_button")
        self.take_snapshot_button.setText("Take Snapshot")
        self.take_snapshot_button.setToolTip("Acquire One Spectrum")
        self.button_layout.addWidget(self.take_snapshot_button)
        self.free_running_button = QtGui.QCheckBox(self.main_frame)
        self.free_running_button.setCheckable(True)
        self.free_running_button.setMaximumWidth(140)
        self.free_running_button.setObjectName("free_running_button")
        self.free_running_button.setText("Free Running Mode")
        self.free_running_button.setToolTip("Acquire New Spectra as Quickly as Possible")
        self.button_layout.addWidget(self.free_running_button)
        spacerItem1 = QtGui.QSpacerItem(400, 520, QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.button_layout.addItem(spacerItem1)
        # Save/load Buttons
        self.save_button = QtGui.QPushButton(self.main_frame)
        self.save_button.setStyleSheet("background-color: rgb(255, 130, 130);")
        self.save_button.setMaximumWidth(200)
        self.save_button.setObjectName("save_button")
        self.save_button.setText("Save Spectrum")
        self.button_layout.addWidget(self.save_button)
        self.load_button = QtGui.QPushButton(self.main_frame)
        self.load_button.setStyleSheet("background-color: rgb(90, 250, 90);")
        self.load_button.setMaximumWidth(200)
        self.load_button.setObjectName("load_button")
        self.load_button.setText("Load Spectrum")
        self.button_layout.addWidget(self.load_button)
        self.vertical_layout.addLayout(self.button_layout)
        self.line = QtGui.QFrame(self.main_frame)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName("line")
        self.vertical_layout.addWidget(self.line)
        self.fit_values_layout = QtGui.QHBoxLayout()
        self.fit_values_layout.setObjectName("fit_values_layout")
        self.curser_value_label = QtGui.QLabel(self.main_frame)
        self.curser_value_label.setObjectName("curser_value_label")
        self.curser_value_label.setText("Curser Wavelength:")
        self.fit_values_layout.addWidget(self.curser_value_label)
        self.label_4 = QtGui.QLabel(self.main_frame)
        self.label_4.setObjectName("label_4")
        self.fit_values_layout.addWidget(self.label_4)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.fit_values_layout.addItem(spacerItem2)
        self.label_6 = QtGui.QLabel(self.main_frame)
        self.label_6.setObjectName("label_6")
        self.label_6.setText("Center:")
        self.fit_values_layout.addWidget(self.label_6)
        self.center_label = QtGui.QLabel(self.main_frame)
        self.center_label.setObjectName("center_label")
        self.fit_values_layout.addWidget(self.center_label)
        self.line_4 = QtGui.QFrame(self.main_frame)
        self.line_4.setFrameShape(QtGui.QFrame.VLine)
        self.line_4.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_4.setObjectName("line_4")
        self.fit_values_layout.addWidget(self.line_4)
        self.label_2 = QtGui.QLabel(self.main_frame)
        self.label_2.setObjectName("label_2")
        self.label_2.setText("FWHM:")
        self.fit_values_layout.addWidget(self.label_2)
        self.fwhm_label = QtGui.QLabel(self.main_frame)
        self.fwhm_label.setObjectName("fwhm_label")
        self.fit_values_layout.addWidget(self.fwhm_label)
        self.line_5 = QtGui.QFrame(self.main_frame)
        self.line_5.setFrameShape(QtGui.QFrame.VLine)
        self.line_5.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_5.setObjectName("line_5")
        self.fit_values_layout.addWidget(self.line_5)
        self.label = QtGui.QLabel(self.main_frame)
        self.label.setObjectName("label")
        self.label.setText("Temp:")
        self.fit_values_layout.addWidget(self.label)
        self.temp_label = QtGui.QLabel(self.main_frame)
        self.temp_label.setObjectName("temp_label")
        self.fit_values_layout.addWidget(self.temp_label)
        self.line_6 = QtGui.QFrame(self.main_frame)
        self.line_6.setFrameShape(QtGui.QFrame.VLine)
        self.line_6.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_6.setObjectName("line_6")
        self.fit_values_layout.addWidget(self.line_6)
        self.label_9 = QtGui.QLabel(self.main_frame)
        self.label_9.setObjectName("label_9")
        self.label_9.setText("Humidity:")
        self.fit_values_layout.addWidget(self.label_9)
        self.humidity_label = QtGui.QLabel(self.main_frame)
        self.humidity_label.setObjectName("humidity_label")
        self.fit_values_layout.addWidget(self.humidity_label)
        self.line_7 = QtGui.QFrame(self.main_frame)
        self.line_7.setFrameShape(QtGui.QFrame.VLine)
        self.line_7.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_7.setObjectName("line_7")
        self.fit_values_layout.addWidget(self.line_7)
        self.label_7 = QtGui.QLabel(self.main_frame)
        self.label_7.setObjectName("label_7")
        self.label_7.setText("Pressure:")
        self.fit_values_layout.addWidget(self.label_7)
        self.pressure_label = QtGui.QLabel(self.main_frame)
        self.pressure_label.setObjectName("pressure_label")
        self.fit_values_layout.addWidget(self.pressure_label)
        self.vertical_layout.addLayout(self.fit_values_layout)
        self.plot_object = pg.PlotWidget()
        self.plot_object.setObjectName("plot_object")
        self.plot_object.getPlotItem().setMouseEnabled(False, False)
        self.curser = pg.InfiniteLine(pos = .00000080000, angle = 90, pen = (75, 100), movable = True)
        self.active_curve = pg.PlotCurveItem(pen=(0,100))
        self.loaded_curve = pg.PlotCurveItem(pen=(35,100))
        self.fit_curve = pg.PlotCurveItem(pen=(10, 100))
        self.plot_object.addItem(self.curser)
        self.plot_object.addItem(self.loaded_curve)
        self.plot_object.addItem(self.active_curve)
        self.plot_object.addItem(self.fit_curve)
        self.plot_object.setLabel('bottom', 'Wavelength', units = 'm')
        self.plot_object.setLabel('left', 'Raw', units = 'arbitrary units')
        self.plot_object.setLimits(xMin = 0.0, xMax = 1200 * 10**-9)
        self.vertical_layout.addWidget(self.plot_object)
        self.setCentralWidget(self.main_frame)
        QtCore.QMetaObject.connectSlotsByName(self)
        # connect all the ui widgets to functions
        self.curser.sigPositionChanged.connect(self.curserMoved)
        self.i_time_box.valueChanged.connect(self.setIntegrationT)
        self.load_cal_button.clicked.connect(self.loadCalibration)
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
        self.timer.start(10000) # update sensor data every 10s
        self.loadConfig()

    # These methods are called as part of startup
    def loadConfig(self):
        try:
            with open(".spec.config", "r") as config_file:
                lines = config_file.readlines()
                self.importCalibration(lines[1][:-1])
                self.importCurve(lines[3][:-1])
                self.blank_data[1] = int(lines[5])
                self.setIntegrationT(verbose = False)
                for index, value in enumerate(lines[7:]):
                    self.blank_data[0][index] = float(value)
        except OSError as e:
            self.updateMessage("**Filename Error - spec.config File Not Properly Imported**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - spec.config File Not Properly Imported**\n" + str(e)[:60])
            print(e)

    def findPorts(self):
        self.ports = serial.tools.list_ports.comports()
        for index, comport in enumerate(self.ports[::-1]):
            self.sensor_port_box.addItem(comport[0])
            self.com_port_box.addItem(comport[0])
            self.sensor_port_box.setItemText(index, comport[1])
            self.com_port_box.setItemText(index, comport[1])
        if len(self.ports) == 0:
            self.updateMessage("**No Available Com Ports Detected**")

    # Close the arduino threads gracefully when the window closes
    def closeEvent(self, evt):
        spec_thread.quit()
        sensor_thread.quit()
        while(not spec_thread.isFinished() or not sensor_thread.isFinished()):
            time.sleep(1)
        QtGui.QMainWindow.closeEvent(self, evt)

    # These methods are for interacting with the graph
    def curserMoved(self):
        xposition = self.curser.value()
        if xposition < 1:
            self.label_4.setText("{0:.2f} nm".format(xposition * 10**9))
        else:
            self.label_4.setText("Pixel No. {}".format(int(xposition)))

    def mousePressEvent(self, evt):
        position = evt.pos()
        if self.plot_object.frameGeometry().contains(position):
            position.setX(position.x() - self.plot_object.frameGeometry().x())
            curser_pos = self.plot_object.getPlotItem().getViewBox().mapSceneToView(position)
            view_range = self.plot_object.getPlotItem().viewRange()[0]
            if curser_pos.x() > view_range[0] and curser_pos.x() < view_range[1]:
                self.curser.setValue(curser_pos)
    # Button press methods
    def takeBlank(self):
        self.is_blank = True
        self.signal.get_spectrum.emit()

    def takeSnapshot(self):
        if(self.free_running):
            self.free_running_button.setChecked(False)
        self.signal.get_spectrum.emit()
        self.updateMessage("Snapshot Initiated - {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))

    def setFreeRunning(self):
        self.free_running = self.free_running_button.isChecked()
        if self.free_running:
            self.updateMessage("Free-Running Mode Enabled")
            self.signal.get_spectrum.emit()
        else:
            self.updateMessage("Free-Running Mode Disabled")

    def loadCalibration(self):
        was_free_running = False
        if(self.free_running):
            self.free_running_button.setChecked(False)
            was_free_running = True
        load_path = QtGui.QFileDialog.getOpenFileName(self, "Select a Calibration Curve File",
                                                      "",
                                                      "Calibration Files (*.cal);;All Files (*.*)")
        if len(load_path) == 0:
            self.updateMessage("**Calibration Loading Cancelled - {}**".format(time.strftime("%Y-%m-%d %H:%M:%S")))
            if was_free_running:
                self.free_running_button.setChecked(True)
            return
        self.importCalibration(load_path)
        # Try saving the calibration filename to the spec.config file
        try:
            with open(".spec.config", "r") as config_file:
                lines = config_file.readlines()
            lines[0] = "Calibration File Last Used:\n"
            lines[1] = str(load_path) + "\n"
            with open(".spec.config", "wt") as config_file:
                config_file.writelines(lines)
        except OSError as e:
            self.updateMessage("**Filename Error - spec.config File Not Properly Written**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - spec.config File Not Properly Written**\n" + str(e)[:60])
            print(e)
        if was_free_running:
            self.free_running_button.setChecked(True)

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
            self.updateActiveData()
            # A calibration file with "Dummy" in the name gives pixel number (from 0 to 2047)
            # To use it we must allow the plot to expand
            if "Dummy" in load_path:
                self.plot_object.setLimits(xMin = -2, xMax = 2050)
                self.plot_object.setLabel('bottom', 'Pixel', units = "")
                #self.plot_object.render()
            else: #But normally, it is better to not allow arbitrary zooming on the plot
                self.plot_object.setLimits(xMin = 0.0, xMax = 1200 * 10**-9)
                self.plot_object.setLabel('bottom', 'Wavelength', units = 'm')
            self.updateMessage("Calibration Loaded Successfully")
        except OSError as e:
            self.updateMessage("**Filename Error - Calibration May Have Not Loded Properly**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - Calibration May Have Not Loaded Properly**\n" + str(e)[:60])
            print(e)

    def loadCurve(self):
        was_free_running = False
        if(self.free_running):
            self.free_running_button.setChecked(False)
            was_free_running = True
        load_path = QtGui.QFileDialog.getOpenFileName(self, "Select a Spectrum to Load",
                                                      "",
                                                      "Spectrum Files (*.csv);;All Files (*.*)")
        if len(load_path) == 0:
            self.updateMessage("**Spectrum Loading Cancelled - {}**".format(time.strftime("%Y-%m-%d %H:%M:%S")))
            if was_free_running:
                self.free_running_button.setChecked(True)
            return
        self.importCurve(load_path)
        # Try saving the loaded filename to the spec.config file
        try:
            with open(".spec.config", "r") as config_file:
                lines = config_file.readlines()
            lines[2] = "Spectrum File Last Loaded:\n"
            lines[3] = str(load_path) + "\n"
            with open(".spec.config", "wt") as config_file:
                config_file.writelines(lines)
        except OSError as e:
            self.updateMessage("**Filename Error - spec.config File Not Properly Written**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - spec.config File Not Properly Written**\n" + str(e)[:60])
            print(e)
        if was_free_running:
            self.free_running_button.setChecked(True)

    def importCurve(self, load_path):
        try:
            with open(load_path, "r") as load_file:
                reader = csv.reader(load_file, dialect = 'excel-tab')
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
            self.updateMessage("Spectrum Loaded - {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))
        except OSError as e:
            self.updateMessage("**Filename Error - Spectrum May Have Not Loded Properly**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - Spectrum May Have Not Loaded Properly**\n" + str(e)[:60])
            print(e)

    def saveCurve(self):
        was_free_running = False
        if(self.free_running):
            self.free_running_button.setChecked(False)
            was_free_running = True
        default_path = time.strftime("%Y-%m-%d_%H:%M:%S")
        save_path = QtGui.QFileDialog.getSaveFileName(self, "Save File As",
                                                      default_path,
                                                      "Spectrum Files (*.csv);;All Files (*.*)")
        if len(save_path) == 0:
            self.updateMessage("**Save Spectrum Cancelled - {}**".format(time.strftime("%Y-%m-%d %H:%M:%S")))
            if was_free_running:
                self.free_running_button.setChecked(True)
            return
        if save_path[-4:] != ".csv":
            save_path = save_path + ".csv"
        try:
            with open(save_path, 'wt') as save_file:
                header = self.generateHeader()
                save_file.write(header)
                writer = csv.writer(save_file, dialect = "excel-tab")
                cal = self.active_data[0]
                dat = self.active_data[1]
                blank = self.blank_data[0]
                for rownum in range(len(cal)):
                    row = [cal[rownum], dat[rownum], blank[rownum]]
                    writer.writerow(row)
            self.updateMessage("Spectrum Saved Successfully")
        except OSError as e:
            self.updateMessage("**Filename Error - Spectrum May Have Not Saved Properly**\n" + str(e)[:60])
            print(e)
        except Exception as e:
            self.updateMessage("**Unknown Error - Spectrum May Have Not Saved Properly**\n" + str(e)[:60])
            print(e)
        if was_free_running:
            self.free_running_button.setChecked(True)

    def setIntegrationT(self, verbose = True):
        i_Time.write(self.i_time_box.value())
        message = self.message_label.text()
        if verbose:
            message = "Integration time set to {} ms - {}".format(self.i_time_box.value(), time.strftime("%Y-%m-%d %H:%M:%S"))
        if self.i_time_box.value() != self.blank_data[1] and self.blank_data[1] != 0:
            message = message + "\n*Current Integration Time is Not the Same as That Used for the Blank ({} ms)- Consider Taking a New Blank*".format(self.blank_data[1])
        self.updateMessage(message)

    def updateMessage(self, message):
        self.message_label.setText(message)

    def getData(self): # A signal says there is new data in spectrum object
        if self.free_running:
            self.signal.get_spectrum.emit() # Start getting the next spectrum right away
        if self.is_blank: # The new data must be from a blank
            self.applyBlank(spectrum.read())
            self.updateMessage("Blank Taken - {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))
            self.is_blank = False
        else:
            self.active_data[1:3] = spectrum.read()
        self.active_data[1] = self.active_data[1] - self.blank_data[0]
        self.updateActiveData()
        self.findFit()

    def applyBlank(self, new_blank):
        # First undo the old blank on the currently active data
        old_blank = self.blank_data
        self.active_data[1] = self.active_data[1] + old_blank[0]
        self.blank_data = new_blank
        self.blankToConfig()

    def clearBlank(self):
        self.applyBlank([np.zeros(2048, float), 0])
        self.updateActiveData()
        self.findFit()
        self.updateMessage("Blank Cleared - {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))

    def blankToConfig(self):
        # Try saving the blank data to the spec.config file
        try:
            with open(".spec.config", "r") as config_file:
                lines = config_file.readlines()
            lines[4] = "Integration Time at Last Blank Taken:\n"
            lines[5] = str(self.blank_data[1]) + "\n"
            lines[6] = "Last Blank Taken:"
            for index, value in enumerate(self.blank_data[0]):
                lines[7 + index] = "\n" + str(value)
            with open(".spec.config", "wt") as config_file:
                config_file.writelines(lines)
        except OSError as e:
            self.updateMessage("**Filename Error - spec.config File Not Properly Written**\n" + str(e)[:60])
        except Exception as e:
            self.updateMessage("**Unknown Error - spec.config File Not Properly Written**\n" + str(e)[:60])
            print(e)

    def getSensorData(self): # A signal says there is new sensor data in the sensor_Data object
        self.temp, self.humidity, self.pressure = sensor_Data.read()
        # This is necessary to properly handle the degree glyph in python 2
        try:
            self.temp_label.setText(QtCore.QString.fromUtf8("{0:.2f} °C".format(self.temp)))
        except Exception:
            self.temp_label.setText("{0:.2f} °C".format(self.temp))
        self.humidity_label.setText("{0:.2f} %".format(self.humidity))
        self.pressure_label.setText("{0:.2f} pa".format(self.pressure))

    def updateActiveData(self):
        self.active_curve.setData(self.active_data[0], self.active_data[1])

    def updateLoadedData(self):
        self.loaded_curve.setData(self.loaded_data[0], self.loaded_data[1])

    def findFit(self):
        amplitude_guess = np.amax(self.active_data[1])
        center_guess = self.active_data[0][1024]
        fwhm_guess = 80 * 10.0**-9.0
        offset_guess = 2.5
        guesses = [amplitude_guess, center_guess, fwhm_guess, offset_guess]
        fit_params, cov = fit(gaussian, self.active_data[0], self.active_data[1], p0 = guesses)
        self.fit_data[1] = gaussian(self.fit_data[0], fit_params[0], fit_params[1], fit_params[2], fit_params[3])
        self.center = fit_params[1]
        self.fwhm = fit_params[2]
        self.fit_curve.setData(self.fit_data[0], self.fit_data[1])
        self.center_label.setText("{0:.2f} nm".format(self.center * 10**9))
        self.fwhm_label.setText("{0:.2f} nm".format(self.fwhm * 10**9))

    def generateHeader(self):
        header = "This spectrum was collected on:\t" + time.strftime("%Y-%m-%d\t%H:%M:%S\n")
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

# These mutex objects communicate between the asynchronous arduino and gui threads
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
        self.value = [0.0,0.0,0.0]  # This is temp, humidity, pressure. they should be floats
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

# These classes handle the communication between arduinos
class Outbound_Signal(QtCore.QObject):
    get_spectrum = QtCore.pyqtSignal()
    get_sensors = QtCore.pyqtSignal()

class Spec_Duino(QtCore.QObject):
    updated = QtCore.pyqtSignal()
    i_time = 5
    def read(self):
        i_time = i_Time.read()
        # this generates a random gaussian dummy spectrum
        amp = 10 + np.random.random() * 50
        center = 875 + np.random.random() * 300
        fwhm = 300 + np.random.random() * 100
        offset = np.random.random() * 4
        data = np.random.uniform(0,1, 2048)
        data = data + gaussian(np.arange(2048), amp, center, fwhm, offset)
        spectrum.write([data, i_time])
        self.updated.emit()

class Sensor_Duino(QtCore.QObject):
    updated = QtCore.pyqtSignal()
    def read(self):
        sensor_Data.write(np.random.uniform(0,12,3))
        self.updated.emit()

# Define a lambda function for use in fitting
gaussian = lambda x, amp, center, fwhm, offset: amp * np.exp(-(x-center)**2/(2*fwhm**2)) + offset

def main():
    # Set the cwd to the Data folder to make it easy in the file dialogs
    file_path = os.path.abspath(__file__)
    folder_path = os.path.dirname(file_path)
    data_path = os.path.join(folder_path, "Data")
    try:
        os.chdir(data_path)
    except:
        folder_path = os.getcwd()
        data_path = os.path.join(folder_path, "Data")
        try:
            os.chdir(data_path)
        except:
            print("**Current Working Directory is NOT the Data Directory**")

    app = QtGui.QApplication(sys.argv)

    # Generate the mutex objects
    global spectrum
    global sensor_Data
    global i_Time
    spectrum = Spectrum()
    sensor_Data = Sensor_Data()
    i_Time = I_Time()

    # Generate the 'duinos and start them in their own threads
    global spec_Duino
    global spec_thread
    global sensor_Duino
    global sensor_thread
    spec_Duino = Spec_Duino()
    spec_thread = QtCore.QThread()
    spec_Duino.moveToThread(spec_thread)
    spec_thread.start()
    sensor_Duino = Sensor_Duino()
    sensor_thread = QtCore.QThread()
    sensor_Duino.moveToThread(sensor_thread)
    sensor_thread.start()

    global MainWindow
    MainWindow = Main_Ui_Window()
    MainWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
    MainWindow.showMaximized()
    app.exec_()
    return MainWindow

main_form = main()