import pathlib
import importlib.metadata
import pydicom
import pytest
from pydicom.fileset import FileSet
from pydicom.valuerep import VR

import dcmrmel.dcmrmel as dcmrmel

THIS_DIR = pathlib.Path(__file__).resolve().parent
TEST_DATA_DIR = THIS_DIR / "test_data"
__version__ = importlib.metadata.version("dcmrmel")

SCRIPT_NAME = "dcmrmel"
SCRIPT_USAGE = f"usage: {SCRIPT_NAME} [-h]"


@pytest.mark.parametrize(
    "args, expected_output",
    [
        ([0, 10, "doing thing"], "doing thing [  0%]\r"),
        ([5, 10], " [ 50%]\r"),
        ([10, 10], " [100%]\n"),
    ],
)
def test_progress(capsys, args, expected_output):
    dcmrmel.progress(*args)
    captured = capsys.readouterr()
    assert captured.out == expected_output


def test_make_dcm_fp_list_error_1(tmp_path, capsys):
    fp_not_dicom = tmp_path / "not_dicom"
    fp_not_dicom.touch()

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        dcmrmel.make_dcm_fp_list(fp_not_dicom)

    assert pytest_wrapped_e.type is SystemExit
    assert pytest_wrapped_e.value.code == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "ERROR: No valid DICOM files found, exiting\n"


def test_make_dcm_fp_list_error_2(tmp_path, capsys):
    fp_not_file = tmp_path / "file_not_exist"

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        dcmrmel.make_dcm_fp_list(fp_not_file)

    assert pytest_wrapped_e.type is SystemExit
    assert pytest_wrapped_e.value.code == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "ERROR: %s is neither a file or directory\n" % fp_not_file


def test_make_dcm_fp_list_file(tmp_path):
    fp_1 = tmp_path / "test_1.dcm"
    ds_1 = pydicom.dataset.Dataset()
    ds_1.StudyDate = "20220101"
    ds_1.PatientBirthDate = "19800101"
    ds_1.PerformedProcedureStepDescription = "MRI Head"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC12345678"
    ds_1.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1.file_meta.ImplementationVersionName = "report"
    ds_1.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_1.file_meta)
    ds_1.save_as(fp_1, implicit_vr=False, little_endian=True, enforce_file_format=True)

    ds_list = dcmrmel.make_dcm_fp_list(fp_1)
    assert ds_list == [fp_1]


def test_make_dcm_fp_list_dir(tmp_path):
    test_dir = tmp_path / "dir1"
    test_dir.mkdir()

    # This shouldn't appear in the list
    fp_not_dicom = test_dir / "not_dicom"
    fp_not_dicom.touch()

    fp_1 = test_dir / "test_1.dcm"
    ds_1 = pydicom.dataset.Dataset()
    ds_1.StudyDate = "20220101"
    ds_1.PatientBirthDate = "19800101"
    ds_1.PerformedProcedureStepDescription = "MRI Head"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC12345678"
    ds_1.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1.file_meta.ImplementationVersionName = "report"
    ds_1.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_1.file_meta)
    ds_1.save_as(fp_1, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fp_2 = test_dir / "test_2.dcm"
    ds_2 = pydicom.dataset.Dataset()
    ds_2.StudyDate = "20220101"
    ds_2.PatientBirthDate = "19800101"
    ds_2.PerformedProcedureStepDescription = "MRI Head"
    ds_2.PatientName = "SURNAME^Firstname"
    ds_2.PatientID = "EFG987654321"
    ds_2.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2.file_meta.ImplementationVersionName = "report"
    ds_2.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_2.file_meta)
    ds_2.save_as(fp_2, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fs = FileSet()
    fp_3 = test_dir / "DICOMDIR"
    fs.write(test_dir)

    ds_list = dcmrmel.make_dcm_fp_list(test_dir)
    assert ds_list == [fp_3, fp_1, fp_2]


def test_remove_tags():
    ds_1 = pydicom.dataset.Dataset()
    ds_1.SOPInstanceUID = pydicom.uid.generate_uid()
    ds_1.StudyDate = "20220101"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC1234567"

    ds_1 = dcmrmel.remove_tags(
        ds_1, [pydicom.tag.Tag("SOPInstanceUID"), pydicom.tag.Tag("StudyDate")]
    )

    ds_remove_ref = pydicom.dataset.Dataset()
    ds_remove_ref.PatientName = "SURNAME^Firstname"
    ds_remove_ref.PatientID = "ABC1234567"

    assert ds_1 == ds_remove_ref


def test_remove_vr_tags():
    ds_1 = pydicom.dataset.Dataset()
    ds_1.SOPInstanceUID = pydicom.uid.generate_uid()
    ds_1.StudyDate = "20220101"
    ds_1.StudyTime = "120000.000000"
    ds_1.Modality = "CT"
    ds_1.StudyDescription = "Study A"
    ds_1.SeriesDescription = "Bone"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC1234567"
    ds_1.StudyInstanceUID = pydicom.uid.generate_uid()
    ds_1.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds_1.SeriesNumber = 1
    ds_1.InstanceNumber = 1

    ds_1 = dcmrmel.remove_vr_tags(ds_1, ["UI", "PN", "DT", "DA", "TM"])

    ds_without_vr_ref = pydicom.dataset.Dataset()
    ds_without_vr_ref.Modality = "CT"
    ds_without_vr_ref.StudyDescription = "Study A"
    ds_without_vr_ref.SeriesDescription = "Bone"
    ds_without_vr_ref.PatientID = "ABC1234567"
    ds_without_vr_ref.SeriesNumber = 1
    ds_without_vr_ref.InstanceNumber = 1

    assert ds_1 == ds_without_vr_ref


def test_remove_group_tags():
    ds_1 = pydicom.dataset.Dataset()
    ds_1.SOPInstanceUID = pydicom.uid.generate_uid()
    ds_1.StudyDate = "20220101"
    ds_1.StudyTime = "120000.000000"
    ds_1.Modality = "CT"
    ds_1.StudyDescription = "Study A"
    ds_1.SeriesDescription = "Bone"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC1234567"
    ds_1.StudyInstanceUID = pydicom.uid.generate_uid()
    ds_1.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds_1.SeriesNumber = 1
    ds_1.InstanceNumber = 1

    ds_1 = dcmrmel.remove_group_tags(ds_1, ["0x0010", "0x0020"])

    ds_without_group10_20_ref = pydicom.dataset.Dataset()
    ds_without_group10_20_ref.SOPInstanceUID = ds_1.SOPInstanceUID
    ds_without_group10_20_ref.StudyDate = "20220101"
    ds_without_group10_20_ref.StudyTime = "120000.000000"
    ds_without_group10_20_ref.Modality = "CT"
    ds_without_group10_20_ref.StudyDescription = "Study A"
    ds_without_group10_20_ref.SeriesDescription = "Bone"

    assert ds_1 == ds_without_group10_20_ref


def test_prints_help_1(script_runner):
    result = script_runner.run([SCRIPT_NAME])
    assert result.success
    assert result.stdout.startswith(SCRIPT_USAGE)


def test_prints_help_2(script_runner):
    result = script_runner.run([SCRIPT_NAME, "-h"])
    assert result.success
    assert result.stdout.startswith(SCRIPT_USAGE)


def test_prints_help_for_invalid_option(script_runner):
    result = script_runner.run([SCRIPT_NAME, "-!"])
    assert not result.success
    assert result.stderr.startswith(SCRIPT_USAGE)


def test_prints_version(script_runner):
    result = script_runner.run([SCRIPT_NAME, "--version"])
    assert result.success
    expected_version_output = SCRIPT_NAME + " " + __version__ + "\n"
    assert result.stdout == expected_version_output


def test_rm_private_with_backup(tmp_path, script_runner):
    test_dir = tmp_path / "dir1"
    test_dir.mkdir()

    # This file should be skipped because it isn't DICOM
    fp_not_dicom = test_dir / "not_dicom"
    fp_not_dicom.touch()

    fp_1 = test_dir / "test_1.dcm"
    ds_1 = pydicom.dataset.Dataset()
    ds_1.StudyDate = "20220101"
    ds_1.PatientBirthDate = "19800101"
    ds_1.PerformedProcedureStepDescription = "MRI Head"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC12345678"
    ds_1.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1.file_meta.ImplementationVersionName = "report"
    ds_1.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_1.file_meta)
    ds_1.save_as(fp_1, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fp_2 = test_dir / "test_2.dcm"
    ds_2 = pydicom.dataset.Dataset()
    ds_2.StudyDate = "20220101"
    ds_2.PatientBirthDate = "19800101"
    ds_2.PerformedProcedureStepDescription = "MRI Head"
    ds_2.PatientName = "SURNAME^Firstname"
    ds_2.PatientID = "EFG987654321"
    ds_2.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2.RepetitionTime = 2000
    ds_2.EchoTime = 10
    block_1 = ds_2.private_block(0x1001, "Test", create=True)
    block_1.add_new(0x01, VR.UL, 42)
    block_1.add_new(0x02, VR.SH, "Hello World")
    block_1.add_new(0x03, VR.UI, "1.2.3.4.5")
    ds_2.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2.file_meta.ImplementationVersionName = "report"
    ds_2.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_2.file_meta)
    ds_2.save_as(fp_2, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fs = FileSet()
    fp_3 = test_dir / "DICOMDIR"
    fs.write(test_dir)

    # Remove all private tags (i.e. only ds_2 will be affected)
    result = script_runner.run([SCRIPT_NAME, str(test_dir), "--rm-private"])
    assert result.success

    # Check non-DICOM and DICOMDIR files remain untouched
    assert fp_not_dicom.is_file()
    assert fp_3.is_file()

    # Check backup files now exist and have identical contents to original input files
    fp_1_bak = test_dir / "test_1.dcm.bak"
    assert fp_1_bak.is_file()
    ds_1_bak = pydicom.dcmread(fp_1_bak)
    assert ds_1 == ds_1_bak

    fp_2_bak = test_dir / "test_2.dcm.bak"
    assert fp_2_bak.is_file()
    ds_2_bak = pydicom.dcmread(fp_2_bak)
    assert ds_2 == ds_2_bak

    ds_2_expected = pydicom.dataset.Dataset()
    ds_2_expected.StudyDate = "20220101"
    ds_2_expected.PatientBirthDate = "19800101"
    ds_2_expected.PerformedProcedureStepDescription = "MRI Head"
    ds_2_expected.PatientName = "SURNAME^Firstname"
    ds_2_expected.PatientID = "EFG987654321"
    ds_2_expected.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2_expected.RepetitionTime = 2000
    ds_2_expected.EchoTime = 10
    ds_2_expected.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2_expected.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2_expected.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2_expected.file_meta.ImplementationVersionName = "report"
    ds_2_expected.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2_expected.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    # Check cleaned output files exist and that the private tags have been removed
    assert fp_1.is_file()
    ds_1_clean = pydicom.dcmread(fp_1)
    # when only the private tags are removed ds_1 remains identical
    assert ds_1_clean == ds_1

    assert fp_2.is_file()
    ds_2_clean = pydicom.dcmread(fp_2)
    assert ds_2_clean == ds_2_expected


def test_rm_private_wo_backup(tmp_path, script_runner):
    test_dir = tmp_path / "dir1"
    test_dir.mkdir()

    # This file should be skipped because it isn't DICOM
    fp_not_dicom = test_dir / "not_dicom"
    fp_not_dicom.touch()

    fp_1 = test_dir / "test_1.dcm"
    ds_1 = pydicom.dataset.Dataset()
    ds_1.StudyDate = "20220101"
    ds_1.PatientBirthDate = "19800101"
    ds_1.PerformedProcedureStepDescription = "MRI Head"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC12345678"
    ds_1.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1.file_meta.ImplementationVersionName = "report"
    ds_1.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_1.file_meta)
    ds_1.save_as(fp_1, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fp_2 = test_dir / "test_2.dcm"
    ds_2 = pydicom.dataset.Dataset()
    ds_2.StudyDate = "20220101"
    ds_2.PatientBirthDate = "19800101"
    ds_2.PerformedProcedureStepDescription = "MRI Head"
    ds_2.PatientName = "SURNAME^Firstname"
    ds_2.PatientID = "EFG987654321"
    ds_2.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2.RepetitionTime = 2000
    ds_2.EchoTime = 10
    block_1 = ds_2.private_block(0x1001, "Test", create=True)
    block_1.add_new(0x01, VR.UL, 42)
    block_1.add_new(0x02, VR.SH, "Hello World")
    block_1.add_new(0x03, VR.UI, "1.2.3.4.5")
    ds_2.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2.file_meta.ImplementationVersionName = "report"
    ds_2.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_2.file_meta)
    ds_2.save_as(fp_2, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fs = FileSet()
    fp_3 = test_dir / "DICOMDIR"
    fs.write(test_dir)

    # Remove all private tags (i.e. only ds_2 will be affected)
    result = script_runner.run(
        [SCRIPT_NAME, str(test_dir), "--no-backup", "--rm-private"]
    )
    assert result.success

    # Check non-DICOM and DICOMDIR files remain untouched
    assert fp_not_dicom.is_file()
    assert fp_3.is_file()

    # Check backup files don't exist
    fp_1_bak = test_dir / "test_1.dcm.bak"
    assert not fp_1_bak.is_file()
    fp_2_bak = test_dir / "test_2.dcm.bak"
    assert not fp_2_bak.is_file()

    ds_2_expected = pydicom.dataset.Dataset()
    ds_2_expected.StudyDate = "20220101"
    ds_2_expected.PatientBirthDate = "19800101"
    ds_2_expected.PerformedProcedureStepDescription = "MRI Head"
    ds_2_expected.PatientName = "SURNAME^Firstname"
    ds_2_expected.PatientID = "EFG987654321"
    ds_2_expected.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2_expected.RepetitionTime = 2000
    ds_2_expected.EchoTime = 10
    ds_2_expected.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2_expected.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2_expected.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2_expected.file_meta.ImplementationVersionName = "report"
    ds_2_expected.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2_expected.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    # Check cleaned output files exist and that the private tags have been removed
    assert fp_1.is_file()
    ds_1_clean = pydicom.dcmread(fp_1)
    # when only the private tags are removed ds_1 remains identical
    assert ds_1_clean == ds_1

    assert fp_2.is_file()
    ds_2_clean = pydicom.dcmread(fp_2)
    assert ds_2_clean == ds_2_expected


def test_rm_vr_with_backup(tmp_path, script_runner):
    # i.e. remove all dates (VR=DA)
    test_dir = tmp_path / "dir1"
    test_dir.mkdir()

    # This file should be skipped because it isn't DICOM
    fp_not_dicom = test_dir / "not_dicom"
    fp_not_dicom.touch()

    fp_1 = test_dir / "test_1.dcm"
    ds_1 = pydicom.dataset.Dataset()
    ds_1.StudyDate = "20220101"
    ds_1.PatientBirthDate = "19800101"
    ds_1.PerformedProcedureStepDescription = "MRI Head"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC12345678"
    ds_1.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1.file_meta.ImplementationVersionName = "report"
    ds_1.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_1.file_meta)
    ds_1.save_as(fp_1, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fp_2 = test_dir / "test_2.dcm"
    ds_2 = pydicom.dataset.Dataset()
    ds_2.StudyDate = "20220101"
    ds_2.PatientBirthDate = "19800101"
    ds_2.PerformedProcedureStepDescription = "MRI Head"
    ds_2.PatientName = "SURNAME^Firstname"
    ds_2.PatientID = "EFG987654321"
    ds_2.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2.RepetitionTime = 2000
    ds_2.EchoTime = 10
    ds_2.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2.file_meta.ImplementationVersionName = "report"
    ds_2.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_2.file_meta)
    ds_2.save_as(fp_2, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fs = FileSet()
    fp_3 = test_dir / "DICOMDIR"
    fs.write(test_dir)

    # Remove elements with DA VR
    result = script_runner.run([SCRIPT_NAME, str(test_dir), "--rm-vr", "DA"])
    assert result.success

    # Check non-DICOM and DICOMDIR files remain untouched
    assert fp_not_dicom.is_file()
    assert fp_3.is_file()

    # Check backup files now exist and have identical contents to original input files
    fp_1_bak = test_dir / "test_1.dcm.bak"
    assert fp_1_bak.is_file()
    ds_1_bak = pydicom.dcmread(fp_1_bak)
    assert ds_1 == ds_1_bak

    fp_2_bak = test_dir / "test_2.dcm.bak"
    assert fp_2_bak.is_file()
    ds_2_bak = pydicom.dcmread(fp_2_bak)
    assert ds_2 == ds_2_bak

    # expected ds with no Dates
    ds_1_expected = pydicom.dataset.Dataset()
    ds_1_expected.PerformedProcedureStepDescription = "MRI Head"
    ds_1_expected.PatientID = "ABC12345678"
    ds_1_expected.PatientName = "SURNAME^Firstname"
    ds_1_expected.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1_expected.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1_expected.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1_expected.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1_expected.file_meta.ImplementationVersionName = "report"
    ds_1_expected.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1_expected.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    ds_2_expected = pydicom.dataset.Dataset()
    ds_2_expected.PerformedProcedureStepDescription = "MRI Head"
    ds_2_expected.PatientID = "EFG987654321"
    ds_2_expected.PatientName = "SURNAME^Firstname"
    ds_2_expected.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2_expected.RepetitionTime = 2000
    ds_2_expected.EchoTime = 10
    ds_2_expected.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2_expected.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2_expected.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2_expected.file_meta.ImplementationVersionName = "report"
    ds_2_expected.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2_expected.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    # Check cleaned output files exist and that the PatientName and Dates have been removed
    assert fp_1.is_file()
    ds_1_clean = pydicom.dcmread(fp_1)
    assert ds_1_clean == ds_1_expected

    assert fp_2.is_file()
    ds_2_clean = pydicom.dcmread(fp_2)
    assert ds_2_clean == ds_2_expected


def test_rm_vr_wo_backup(tmp_path, script_runner):
    # i.e. remove all dates (VR=DA)
    test_dir = tmp_path / "dir1"
    test_dir.mkdir()

    # This file should be skipped because it isn't DICOM
    fp_not_dicom = test_dir / "not_dicom"
    fp_not_dicom.touch()

    fp_1 = test_dir / "test_1.dcm"
    ds_1 = pydicom.dataset.Dataset()
    ds_1.StudyDate = "20220101"
    ds_1.PatientBirthDate = "19800101"
    ds_1.PerformedProcedureStepDescription = "MRI Head"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC12345678"
    ds_1.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1.file_meta.ImplementationVersionName = "report"
    ds_1.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_1.file_meta)
    ds_1.save_as(fp_1, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fp_2 = test_dir / "test_2.dcm"
    ds_2 = pydicom.dataset.Dataset()
    ds_2.StudyDate = "20220101"
    ds_2.PatientBirthDate = "19800101"
    ds_2.PerformedProcedureStepDescription = "MRI Head"
    ds_2.PatientName = "SURNAME^Firstname"
    ds_2.PatientID = "EFG987654321"
    ds_2.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2.RepetitionTime = 2000
    ds_2.EchoTime = 10
    ds_2.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2.file_meta.ImplementationVersionName = "report"
    ds_2.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_2.file_meta)
    ds_2.save_as(fp_2, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fs = FileSet()
    fp_3 = test_dir / "DICOMDIR"
    fs.write(test_dir)

    # Remove elements with DA VR
    result = script_runner.run(
        [SCRIPT_NAME, str(test_dir), "--no-backup", "--rm-vr", "DA"]
    )
    assert result.success

    # Check non-DICOM and DICOMDIR files remain untouched
    assert fp_not_dicom.is_file()
    assert fp_3.is_file()

    # Check backup files don't exist
    fp_1_bak = test_dir / "test_1.dcm.bak"
    assert not fp_1_bak.is_file()
    fp_2_bak = test_dir / "test_2.dcm.bak"
    assert not fp_2_bak.is_file()

    # expected ds with no Dates
    ds_1_expected = pydicom.dataset.Dataset()
    ds_1_expected.PerformedProcedureStepDescription = "MRI Head"
    ds_1_expected.PatientID = "ABC12345678"
    ds_1_expected.PatientName = "SURNAME^Firstname"
    ds_1_expected.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1_expected.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1_expected.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1_expected.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1_expected.file_meta.ImplementationVersionName = "report"
    ds_1_expected.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1_expected.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    ds_2_expected = pydicom.dataset.Dataset()
    ds_2_expected.PerformedProcedureStepDescription = "MRI Head"
    ds_2_expected.PatientID = "EFG987654321"
    ds_2_expected.PatientName = "SURNAME^Firstname"
    ds_2_expected.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2_expected.RepetitionTime = 2000
    ds_2_expected.EchoTime = 10
    ds_2_expected.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2_expected.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2_expected.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2_expected.file_meta.ImplementationVersionName = "report"
    ds_2_expected.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2_expected.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    # Check cleaned output files exist and that the PatientName and Dates have been removed
    assert fp_1.is_file()
    ds_1_clean = pydicom.dcmread(fp_1)
    assert ds_1_clean == ds_1_expected

    assert fp_2.is_file()
    ds_2_clean = pydicom.dcmread(fp_2)
    assert ds_2_clean == ds_2_expected


def test_rm_group_with_backup(tmp_path, script_runner):
    # Remove group 0018 i.e. RepetitionTime and EchoTime
    # these are only in ds_2 so ds_1 should be untouched

    test_dir = tmp_path / "dir1"
    test_dir.mkdir()

    # This file should be skipped because it isn't DICOM
    fp_not_dicom = test_dir / "not_dicom"
    fp_not_dicom.touch()

    fp_1 = test_dir / "test_1.dcm"
    ds_1 = pydicom.dataset.Dataset()
    ds_1.StudyDate = "20220101"
    ds_1.PatientBirthDate = "19800101"
    ds_1.PerformedProcedureStepDescription = "MRI Head"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC12345678"
    ds_1.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1.file_meta.ImplementationVersionName = "report"
    ds_1.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_1.file_meta)
    ds_1.save_as(fp_1, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fp_2 = test_dir / "test_2.dcm"
    ds_2 = pydicom.dataset.Dataset()
    ds_2.StudyDate = "20220101"
    ds_2.PatientBirthDate = "19800101"
    ds_2.PerformedProcedureStepDescription = "MRI Head"
    ds_2.PatientName = "SURNAME^Firstname"
    ds_2.PatientID = "EFG987654321"
    ds_2.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2.RepetitionTime = 2000
    ds_2.EchoTime = 10
    ds_2.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2.file_meta.ImplementationVersionName = "report"
    ds_2.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_2.file_meta)
    ds_2.save_as(fp_2, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fs = FileSet()
    fp_3 = test_dir / "DICOMDIR"
    fs.write(test_dir)

    # Remove elements with DT VR, the PatientName tag,  group 18 (i.e. RepetitionTime and EchoTime) and any private tags
    result = script_runner.run([SCRIPT_NAME, str(test_dir), "--rm-group", "0x0018"])
    assert result.success

    # Check non-DICOM and DICOMDIR files remain untouched
    assert fp_not_dicom.is_file()
    assert fp_3.is_file()

    # Check backup files now exist and have identical contents to original input files
    fp_1_bak = test_dir / "test_1.dcm.bak"
    assert fp_1_bak.is_file()
    ds_1_bak = pydicom.dcmread(fp_1_bak)
    assert ds_1 == ds_1_bak

    fp_2_bak = test_dir / "test_2.dcm.bak"
    assert fp_2_bak.is_file()
    ds_2_bak = pydicom.dcmread(fp_2_bak)
    assert ds_2 == ds_2_bak

    # expected ds with no group 0018
    ds_2_expected = pydicom.dataset.Dataset()
    ds_2_expected.StudyDate = "20220101"
    ds_2_expected.PatientBirthDate = "19800101"
    ds_2_expected.PerformedProcedureStepDescription = "MRI Head"
    ds_2_expected.PatientID = "EFG987654321"
    ds_2_expected.PatientName = "SURNAME^Firstname"
    ds_2_expected.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2_expected.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2_expected.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2_expected.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2_expected.file_meta.ImplementationVersionName = "report"
    ds_2_expected.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2_expected.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    # Check cleaned output files exist and that the PatientName and Dates have been removed
    assert fp_1.is_file()
    ds_1_clean = pydicom.dcmread(fp_1)
    assert ds_1_clean == ds_1

    assert fp_2.is_file()
    ds_2_clean = pydicom.dcmread(fp_2)
    assert ds_2_clean == ds_2_expected


def test_rm_group_wo_backup(tmp_path, script_runner):
    # Remove group 0018 i.e. RepetitionTime and EchoTime
    # these are only in ds_2 so ds_1 should be untouched

    test_dir = tmp_path / "dir1"
    test_dir.mkdir()

    # This file should be skipped because it isn't DICOM
    fp_not_dicom = test_dir / "not_dicom"
    fp_not_dicom.touch()

    fp_1 = test_dir / "test_1.dcm"
    ds_1 = pydicom.dataset.Dataset()
    ds_1.StudyDate = "20220101"
    ds_1.PatientBirthDate = "19800101"
    ds_1.PerformedProcedureStepDescription = "MRI Head"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC12345678"
    ds_1.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1.file_meta.ImplementationVersionName = "report"
    ds_1.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_1.file_meta)
    ds_1.save_as(fp_1, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fp_2 = test_dir / "test_2.dcm"
    ds_2 = pydicom.dataset.Dataset()
    ds_2.StudyDate = "20220101"
    ds_2.PatientBirthDate = "19800101"
    ds_2.PerformedProcedureStepDescription = "MRI Head"
    ds_2.PatientName = "SURNAME^Firstname"
    ds_2.PatientID = "EFG987654321"
    ds_2.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2.RepetitionTime = 2000
    ds_2.EchoTime = 10
    ds_2.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2.file_meta.ImplementationVersionName = "report"
    ds_2.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_2.file_meta)
    ds_2.save_as(fp_2, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fs = FileSet()
    fp_3 = test_dir / "DICOMDIR"
    fs.write(test_dir)

    # Remove elements with DT VR, the PatientName tag,  group 18 (i.e. RepetitionTime and EchoTime) and any private tags
    result = script_runner.run(
        [SCRIPT_NAME, str(test_dir), "--no-backup", "--rm-group", "0x0018"]
    )
    assert result.success

    # Check non-DICOM and DICOMDIR files remain untouched
    assert fp_not_dicom.is_file()
    assert fp_3.is_file()

    # Check backup files don't exist
    fp_1_bak = test_dir / "test_1.dcm.bak"
    assert not fp_1_bak.is_file()
    fp_2_bak = test_dir / "test_2.dcm.bak"
    assert not fp_2_bak.is_file()

    # expected ds with no group 0018
    ds_2_expected = pydicom.dataset.Dataset()
    ds_2_expected.StudyDate = "20220101"
    ds_2_expected.PatientBirthDate = "19800101"
    ds_2_expected.PerformedProcedureStepDescription = "MRI Head"
    ds_2_expected.PatientID = "EFG987654321"
    ds_2_expected.PatientName = "SURNAME^Firstname"
    ds_2_expected.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2_expected.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2_expected.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2_expected.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2_expected.file_meta.ImplementationVersionName = "report"
    ds_2_expected.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2_expected.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    # Check cleaned output files exist and that the PatientName and Dates have been removed
    assert fp_1.is_file()
    ds_1_clean = pydicom.dcmread(fp_1)
    assert ds_1_clean == ds_1

    assert fp_2.is_file()
    ds_2_clean = pydicom.dcmread(fp_2)
    assert ds_2_clean == ds_2_expected


def test_rm_tag_with_backup(tmp_path, script_runner):
    # remove patient name tag
    test_dir = tmp_path / "dir1"
    test_dir.mkdir()

    # This file should be skipped because it isn't DICOM
    fp_not_dicom = test_dir / "not_dicom"
    fp_not_dicom.touch()

    fp_1 = test_dir / "test_1.dcm"
    ds_1 = pydicom.dataset.Dataset()
    ds_1.StudyDate = "20220101"
    ds_1.PatientBirthDate = "19800101"
    ds_1.PerformedProcedureStepDescription = "MRI Head"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC12345678"
    ds_1.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1.file_meta.ImplementationVersionName = "report"
    ds_1.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_1.file_meta)
    ds_1.save_as(fp_1, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fp_2 = test_dir / "test_2.dcm"
    ds_2 = pydicom.dataset.Dataset()
    ds_2.StudyDate = "20220101"
    ds_2.PatientBirthDate = "19800101"
    ds_2.PerformedProcedureStepDescription = "MRI Head"
    ds_2.PatientName = "SURNAME^Firstname"
    ds_2.PatientID = "EFG987654321"
    ds_2.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2.RepetitionTime = 2000
    ds_2.EchoTime = 10
    ds_2.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2.file_meta.ImplementationVersionName = "report"
    ds_2.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_2.file_meta)
    ds_2.save_as(fp_2, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fs = FileSet()
    fp_3 = test_dir / "DICOMDIR"
    fs.write(test_dir)

    # Remove elements with DT VR, the PatientName tag,  group 18 (i.e. RepetitionTime and EchoTime) and any private tags
    result = script_runner.run([SCRIPT_NAME, str(test_dir), "--rm-tag", "PatientName"])
    assert result.success

    # Check non-DICOM and DICOMDIR files remain untouched
    assert fp_not_dicom.is_file()
    assert fp_3.is_file()

    # Check backup files now exist and have identical contents to original input files
    fp_1_bak = test_dir / "test_1.dcm.bak"
    assert fp_1_bak.is_file()
    ds_1_bak = pydicom.dcmread(fp_1_bak)
    assert ds_1 == ds_1_bak

    fp_2_bak = test_dir / "test_2.dcm.bak"
    assert fp_2_bak.is_file()
    ds_2_bak = pydicom.dcmread(fp_2_bak)
    assert ds_2 == ds_2_bak

    # expected ds with no PatientName and no Dates
    ds_1_expected = pydicom.dataset.Dataset()
    ds_1_expected.StudyDate = "20220101"
    ds_1_expected.PatientBirthDate = "19800101"
    ds_1_expected.PerformedProcedureStepDescription = "MRI Head"
    ds_1_expected.PatientID = "ABC12345678"
    ds_1_expected.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1_expected.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1_expected.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1_expected.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1_expected.file_meta.ImplementationVersionName = "report"
    ds_1_expected.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1_expected.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    ds_2_expected = pydicom.dataset.Dataset()
    ds_2_expected.StudyDate = "20220101"
    ds_2_expected.PatientBirthDate = "19800101"
    ds_2_expected.PerformedProcedureStepDescription = "MRI Head"
    ds_2_expected.PatientID = "EFG987654321"
    ds_2_expected.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2_expected.RepetitionTime = 2000
    ds_2_expected.EchoTime = 10
    ds_2_expected.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2_expected.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2_expected.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2_expected.file_meta.ImplementationVersionName = "report"
    ds_2_expected.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2_expected.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    # Check cleaned output files exist and that the PatientName and Dates have been removed
    assert fp_1.is_file()
    ds_1_clean = pydicom.dcmread(fp_1)
    assert ds_1_clean == ds_1_expected

    assert fp_2.is_file()
    ds_2_clean = pydicom.dcmread(fp_2)
    assert ds_2_clean == ds_2_expected


def test_rm_tag_wo_backup(tmp_path, script_runner):
    # remove patient name tag
    test_dir = tmp_path / "dir1"
    test_dir.mkdir()

    # This file should be skipped because it isn't DICOM
    fp_not_dicom = test_dir / "not_dicom"
    fp_not_dicom.touch()

    fp_1 = test_dir / "test_1.dcm"
    ds_1 = pydicom.dataset.Dataset()
    ds_1.StudyDate = "20220101"
    ds_1.PatientBirthDate = "19800101"
    ds_1.PerformedProcedureStepDescription = "MRI Head"
    ds_1.PatientName = "SURNAME^Firstname"
    ds_1.PatientID = "ABC12345678"
    ds_1.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1.file_meta.ImplementationVersionName = "report"
    ds_1.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_1.file_meta)
    ds_1.save_as(fp_1, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fp_2 = test_dir / "test_2.dcm"
    ds_2 = pydicom.dataset.Dataset()
    ds_2.StudyDate = "20220101"
    ds_2.PatientBirthDate = "19800101"
    ds_2.PerformedProcedureStepDescription = "MRI Head"
    ds_2.PatientName = "SURNAME^Firstname"
    ds_2.PatientID = "EFG987654321"
    ds_2.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2.RepetitionTime = 2000
    ds_2.EchoTime = 10
    ds_2.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2.file_meta.ImplementationVersionName = "report"
    ds_2.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    pydicom.dataset.validate_file_meta(ds_2.file_meta)
    ds_2.save_as(fp_2, implicit_vr=False, little_endian=True, enforce_file_format=True)

    fs = FileSet()
    fp_3 = test_dir / "DICOMDIR"
    fs.write(test_dir)

    # Remove elements with DT VR, the PatientName tag,  group 18 (i.e. RepetitionTime and EchoTime) and any private tags
    result = script_runner.run(
        [SCRIPT_NAME, str(test_dir), "--no-backup", "--rm-tag", "PatientName"]
    )
    assert result.success

    # Check non-DICOM and DICOMDIR files remain untouched
    assert fp_not_dicom.is_file()
    assert fp_3.is_file()

    # Check backup files don't exist
    fp_1_bak = test_dir / "test_1.dcm.bak"
    assert not fp_1_bak.is_file()
    fp_2_bak = test_dir / "test_2.dcm.bak"
    assert not fp_2_bak.is_file()

    # expected ds with no PatientName and no Dates
    ds_1_expected = pydicom.dataset.Dataset()
    ds_1_expected.StudyDate = "20220101"
    ds_1_expected.PatientBirthDate = "19800101"
    ds_1_expected.PerformedProcedureStepDescription = "MRI Head"
    ds_1_expected.PatientID = "ABC12345678"
    ds_1_expected.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_1_expected.file_meta = pydicom.dataset.FileMetaDataset()
    ds_1_expected.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_1_expected.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds_1_expected.file_meta.ImplementationVersionName = "report"
    ds_1_expected.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_1_expected.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    ds_2_expected = pydicom.dataset.Dataset()
    ds_2_expected.StudyDate = "20220101"
    ds_2_expected.PatientBirthDate = "19800101"
    ds_2_expected.PerformedProcedureStepDescription = "MRI Head"
    ds_2_expected.PatientID = "EFG987654321"
    ds_2_expected.ReferringPhysicianName = "DrSURNAME^DrFirstname"
    ds_2_expected.RepetitionTime = 2000
    ds_2_expected.EchoTime = 10
    ds_2_expected.file_meta = pydicom.dataset.FileMetaDataset()
    ds_2_expected.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
    ds_2_expected.file_meta.MediaStorageSOPInstanceUID = "4.5.6.7"
    ds_2_expected.file_meta.ImplementationVersionName = "report"
    ds_2_expected.file_meta.ImplementationClassUID = "1.2.3.4"
    ds_2_expected.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"

    # Check cleaned output files exist and that the PatientName and Dates have been removed
    assert fp_1.is_file()
    ds_1_clean = pydicom.dcmread(fp_1)
    assert ds_1_clean == ds_1_expected

    assert fp_2.is_file()
    ds_2_clean = pydicom.dcmread(fp_2)
    assert ds_2_clean == ds_2_expected
