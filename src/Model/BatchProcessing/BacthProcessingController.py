from src.Model.BatchProcessing.BatchImageLoader import BatchImageLoader


class BatchProcessingController:

    def __init__(self, dicom_structure):
        self.dicom_structure = dicom_structure

    def start_processing(self, interrupt_flag, progress_callback):
        for patient in self.dicom_structure.patients.values():
            cur_patient_files = patient.get_files()

            image_loader = BatchImageLoader(cur_patient_files, self)
            patient_dict_container = image_loader.load(interrupt_flag, progress_callback)

