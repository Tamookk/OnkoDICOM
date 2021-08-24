import os

from pydicom import dcmread

from src.Model import ImageLoading
from src.Model.BatchProcessing.BatchPatientDictContainer import BatchPatientDictContainer


class BatchImageLoader:
    """
    This class is responsible for initializing and creating all the values required to create an instance of
    the PatientDictContainer, that is used to store all the DICOM-related data used to create the patient window.
    """
    def __init__(self, selected_files):
        self.selected_files = selected_files

    def load(self, interrupt_flag, progress_callback):
        """
        :param interrupt_flag: A threading.Event() object that tells the function to stop loading.
        :param progress_callback: A signal that receives the current progress of the loading.
        :return: PatientDictContainer object containing all values related to the loaded DICOM files.
        """
        progress_callback.emit(("Creating dataset...", 0))
        try:
            path = os.path.dirname(os.path.commonprefix(self.selected_files))  # Gets the common root folder.
            read_data_dict, file_names_dict = ImageLoading.get_datasets(self.selected_files)
        except ImageLoading.NotAllowedClassError:
            raise ImageLoading.NotAllowedClassError

        # Populate the initial values in the PatientDictContainer singleton.
        patient_dict_container = BatchPatientDictContainer()
        patient_dict_container.set_initial_values(path, read_data_dict, file_names_dict)

        # As there is no way to interrupt a QRunnable, this method must check after every step whether or not the
        # interrupt flag has been set, in which case it will interrupt this method after the currently processing
        # function has finished running. It's not very pretty, and the thread will still run some functions for, in some
        # cases, up to a couple seconds after the close button on the Progress Window has been clicked, however it's
        # the best solution I could come up with. If you have a cleaner alternative, please make your contribution.
        if interrupt_flag.is_set():
            print("stopped")
            return False

        if 'rtss' in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])

            progress_callback.emit(("Getting ROI info...", 10))
            rois = ImageLoading.get_roi_info(dataset_rtss)

            if interrupt_flag.is_set():  # Stop loading.
                print("stopped")
                return False

            progress_callback.emit(("Getting contour data...", 30))
            dict_raw_contour_data, dict_numpoints = ImageLoading.get_raw_contour_data(dataset_rtss)

            if interrupt_flag.is_set():  # Stop loading.
                print("stopped")
                return False

            progress_callback.emit(("Getting pixel LUTs...", 50))
            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            if interrupt_flag.is_set():  # Stop loading.
                print("stopped")
                return False

            # Add RTSS values to PatientDictContainer
            patient_dict_container.set("rois", rois)
            patient_dict_container.set("raw_contour", dict_raw_contour_data)
            patient_dict_container.set("num_points", dict_numpoints)
            patient_dict_container.set("pixluts", dict_pixluts)

        return patient_dict_container
