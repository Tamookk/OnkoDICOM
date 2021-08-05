from src.Model.BatchProcessing.BatchImageLoader import BatchImageLoader
from pathlib import Path
import os
from src.Model.GetPatientInfo import DicomTree
from src.Model.ISO2ROI import ISO2ROI
from src.Model import ImageLoading
from src.Model import InitialModel

class BatchProcessingController:

    def __init__(self, dicom_structure, processes):
        self.dicom_structure = dicom_structure
        self.processes = processes

    def start_processing(self, interrupt_flag, progress_callback):
        for patient in self.dicom_structure.patients.values():
            cur_patient_files = patient.get_files()

            progress_callback.emit(("Setting up files .. ", 60))

            image_loader = BatchImageLoader(cur_patient_files)
            patient_dict_container = image_loader.load(interrupt_flag, progress_callback)

            InitialModel.create_initial_model(patient_dict_container)

            if "iso2roi" in self.processes:
                progress_callback.emit(("Performing ISO2ROI .. ", 70))
                self.start_process_iso2roi(patient_dict_container)
                progress_callback.emit(("Completed ISO2ROI .. ", 80))

            if "suv2roi" in self.processes:
                # Perform suv2roi on patient
                pass

    def start_process_iso2roi(self, patient_dict_container):
        """
        Initiates iso2roi conversion process
        """
        # Ensure dataset is a complete DICOM-RT object
        val = ImageLoading.is_dataset_dicom_rt(patient_dict_container.dataset)

        iso2roi = ISO2ROI(patient_dict_container, False)

        if val:
            print("Dataset is complete")
        else:
            print("Not complete")
            # Check if RT struct file is missing. If yes, create one and
            # add its data to the patient dict container
            if not patient_dict_container.get("file_rtss"):
                # Get common directory
                file_path = patient_dict_container.filepaths.values()
                file_path = Path(os.path.commonpath(file_path))

                # Create RT Struct file
                ds = iso2roi.generate_rtss(file_path)

                # Get new RT Struct file path
                file_path = str(file_path.joinpath("rtss.dcm"))

                # Add RT Struct file path to patient dict container
                patient_dict_container.filepaths['rtss'] = file_path
                filepaths = patient_dict_container.filepaths

                # Add RT Struct dataset to patient dict container
                patient_dict_container.dataset['rtss'] = ds
                dataset = patient_dict_container.dataset

                # Set some patient dict container attributes
                patient_dict_container.set("file_rtss", filepaths['rtss'])
                patient_dict_container.set("dataset_rtss", dataset['rtss'])

                dicom_tree_rtss = DicomTree(filepaths['rtss'])
                patient_dict_container.set("dict_dicom_tree_rtss", dicom_tree_rtss.dict)

                patient_dict_container.set("selected_rois", [])
                patient_dict_container.set("dict_polygons", {})

        # Get isodose levels to turn into ROIs
        iso2roi.get_iso_levels()

        # Calculate dose boundaries
        print("Calculating boundaries")
        boundaries = iso2roi.calculate_boundaries()

        # Return if boundaries could not be calculated
        if not boundaries:
            print("Boundaries could not be calculated.")
            return

        print("Generating ROIs")
        iso2roi.generate_roi(boundaries)
        print("Done")