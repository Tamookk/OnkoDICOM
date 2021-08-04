import threading

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

from src.Model import ImageLoading
from src.Model.Worker import Worker
from src.Model.BatchProcessing.BatchImageLoader import BatchImageLoader
from src.Model.BatchProcessing.BacthProcessingController import BatchProcessingController


class BatchProgressWindow(QDialog):
    signal_loaded = QtCore.Signal()
    signal_error = QtCore.Signal(int)

    def __init__(self, *args, **kwargs):
        super(BatchProgressWindow, self).__init__(*args, **kwargs)

        # Setting up progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setGeometry(10, 50, 230, 20)
        self.progress_bar.setMaximum(100)

        self.setWindowTitle("Loading")
        self.setFixedSize(248, 80)

        self.text_field = QLabel("Loading")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.text_field)
        self.layout.addWidget(self.progress_bar)
        self.setLayout(self.layout)

        self.threadpool = QThreadPool()
        self.interrupt_flag = threading.Event()

    def start_processing(self, dicom_structure):
        batch_processing_controller = BatchProcessingController(dicom_structure)

        worker = Worker(batch_processing_controller.start_processing, self.interrupt_flag, progress_callback=True)
        worker.signals.result.connect(self.on_finish)
        worker.signals.error.connect(self.on_error)
        worker.signals.progress.connect(self.update_progress)

        self.threadpool.start(worker)

    def on_finish(self):
        self.signal_loaded.emit()

    def update_progress(self, progress_update):
        """
        Function responsible for updating the bar percentage and the label.
        :param progress_update: A tuple containing update text and update percentage
        """
        self.text_field.setText(progress_update[0])
        self.progress_bar.setValue(progress_update[1])

    def on_error(self, err):
        if type(err[1]) is ImageLoading.NotRTSetError:
            self.signal_error.emit(0)
        elif type(err[1]) is ImageLoading.NotAllowedClassError:
            self.signal_error.emit(1)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.interrupt_flag.set()
