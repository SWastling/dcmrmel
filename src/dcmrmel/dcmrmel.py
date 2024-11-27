import argparse
import importlib.metadata
import os
import sys
import pydicom
import pathlib
import shutil

__version__ = importlib.metadata.version("dcmrmel")


def progress(count, total, message=None):
    """
    Print percentage progress to stdout during loop.

    :param count: Loop counter
    :type count: int
    :param total: Total number of iterations of loop
    :type total: str
    :param message: Optional message to accompany % progress
    :type message: str
    """
    if message is None:
        message = ""

    percents = round(100.0 * count / float(total), 1)

    if total == count:
        print("%s [%3d%%]" % (message, percents))
    else:
        print("%s [%3d%%]" % (message, percents), end="\r")


def make_dcm_fp_list(pth):
    """
    Create a list of DICOM file-paths

    :param pth: File or directory
    :type pth: pathlib.Path
    :return: List of DICOM file-paths
    :rtype: list[pathlib.Path]
    """

    fp_list = []
    if pth.is_file():
        if pydicom.misc.is_dicom(pth):
            fp_list.append(pth)
    elif pth.is_dir():
        for root, _, files in os.walk(pth):
            for fn in files:
                fp = pathlib.Path(root) / fn
                if pydicom.misc.is_dicom(fp):
                    fp_list.append(fp)
    else:
        sys.stderr.write("ERROR: %s is neither a file or directory\n" % pth)
        sys.exit(1)

    if len(fp_list) == 0:
        sys.stderr.write("ERROR: No valid DICOM files found, exiting\n")
        sys.exit(1)

    return fp_list


def remove_tags(ds, tags_to_rm):
    """
    Remove selected tags from DICOM dataset

    :param ds: DICOM dataset
    :type ds: pydicom.dataset.Dataset
    :param tags_to_rm: list of tags to remove
    :type tags_to_rm: list[pydicom.tag.BaseTag]
    :return: DICOM dataset with tags removed
    :rtype: pydicom.dataset.Dataset
    """

    def callback(ds_a, elem):
        if elem.tag in tags_to_rm:
            del ds_a[elem.tag]

    ds.walk(callback)

    return ds


def remove_vr_tags(ds, vrs_to_remove):
    """
    Remove tags with a given value representation (VR) from DICOM dataset

    :param ds: DICOM dataset
    :type ds: pydicom.dataset.Dataset
    :param vrs_to_remove: list of value representations (VR) of tags to remove
    :type vrs_to_remove: list[str]
    :return: DICOM dataset with tags removed
    :rtype: pydicom.dataset.Dataset
    """

    def callback(ds_a, elem):
        if elem.VR in vrs_to_remove:
            del ds_a[elem.tag]

    ds.walk(callback)
    return ds


def remove_group_tags(ds, groups_to_remove):
    """
    Remove tags in a given group from DICOM dataset

    :param ds: DICOM dataset
    :type ds: pydicom.dataset.Dataset
    :param groups_to_remove: group to remove as hex str e.g. 0x10
    :type groups_to_remove: list[str]
    :return: DICOM dataset with tags removed
    :rtype: pydicom.dataset.Dataset
    """
    group_rm = []
    for group in groups_to_remove:
        group_rm.append(int(group, 16))

    def callback(ds_a, elem):
        if elem.tag.group in group_rm:
            del ds_a[elem.tag]

    ds.walk(callback)
    return ds


def main():
    parser = argparse.ArgumentParser(
        description="Remove element(s) from DICOM dataset(s)"
    )

    parser.add_argument(
        "d",
        help="DICOM file or directory containing DICOM files",
        type=pathlib.Path,
        metavar="FILE or DIR",
    )

    parser.add_argument(
        "--no-backup",
        dest="no_backup",
        help="don't backup files before removing elements (DANGEROUS)",
        action="store_true",
    )

    parser.add_argument(
        "--rm-private",
        dest="rm_private",
        help="remove all elements with an odd group number",
        action="store_true",
    )

    parser.add_argument(
        "--rm-vr",
        dest="rm_vr",
        help="list of value-representations to remove (e.g. AS, AT,"
        " CS, DA, DS, DT, FL, FD, IS, LO, LT, OB, OD, OF, OW, PN, SH, SL,"
        " SQ, SS, ST, TM, UI, UL, UN, US or UT)",
        nargs="+",
        type=str,
        metavar="VR",
    )

    parser.add_argument(
        "--rm-group",
        dest="rm_group",
        help="list of groups to remove (e.g. 0x0008 or 0x0010 etc...)",
        nargs="+",
        type=str,
        metavar="GROUP",
    )

    parser.add_argument(
        "--rm-tag",
        dest="rm_tag",
        help="list of tags to remove. Tags can be keywords e.g. RepetitionTime "
        "or combined group and element numbers e.g. 0x00180080",
        nargs="+",
        type=str,
        metavar="TAG",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    if len(sys.argv) == 1:
        sys.argv.append("-h")

    args = parser.parse_args()

    fp_list = make_dcm_fp_list(args.d)

    for fp_cnt, fp in enumerate(fp_list, 1):
        progress(
            fp_cnt,
            len(fp_list),
            "* removing tags from %d files" % (len(fp_list)),
        )

        ds = pydicom.dcmread(fp)
        sop_class = ds.file_meta.get("MediaStorageSOPClassUID", None)
        if sop_class == pydicom.uid.MediaStorageDirectoryStorage:
            continue

        if not args.no_backup:
            fp_bak = fp.with_suffix(fp.suffix + ".bak")
            shutil.copy(fp, fp_bak)

        if args.rm_private:
            ds.remove_private_tags()

        if args.rm_vr is not None:
            ds = remove_vr_tags(ds, args.rm_vr)
            ds.file_meta = remove_vr_tags(ds.file_meta, args.rm_vr)

        if args.rm_group is not None:
            ds = remove_group_tags(ds, args.rm_group)
            ds.file_meta = remove_group_tags(ds.file_meta, args.rm_group)

        if args.rm_tag:
            tag_to_rm_list = []
            for tag_to_rm in args.rm_tag:
                tag_to_rm_list.append(pydicom.tag.Tag(tag_to_rm))

            ds = remove_tags(ds, tag_to_rm_list)
            ds.file_meta = remove_tags(ds.file_meta, tag_to_rm_list)

        ds.save_as(fp)


if __name__ == "__main__":  # pragma: no cover
    main()
