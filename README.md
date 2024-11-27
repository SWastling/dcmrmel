# dcmrmel

## Synopsis
Delete element(s) from DICOM file(s)

## Usage

```bash
dcmrmel [options] FILE or DIR
```
- `FILE or DIR`: DICOM file or directory

## Options
- `-h`: display help message
- `--no-backup`: don't backup files before removing elements (DANGEROUS)
- `--rm-private`: remove all elements with an odd group number
- `--rm-vr`: list of value-representations to remove (e.g. AS, AT, CS, 
DA, DS, DT, FL, FD, IS, LO, LT, OB, OD, OF, OW, PN, SH, SL, SQ, SS, ST, TM, UI, 
UL, UN, US or UT)
- `--rm-group`: list of groups to remove (e.g. 0x0008 or 0x0010)
- `--rm-tag`: list of tags to remove. Tags can be keywords e.g. 
RepetitionTime or combined group and element numbers e.g. 0x00180080
- `--version`: show version

> [!CAUTION]
> The `--no-backup` option means that `dcmrmel` does **NOT** make a copy of 
> the files before the elements are deleted.  

> [!CAUTION]
> Since `dcmrmel` can delete _any_ element(s) and given that the files produced 
> are **NOT** verified against the requirements of the IODs and Modules defined 
> in DICOM PS 3.3 the files may not by handled correctly by other programs 
> expecting valid DICOM.  

## Description
dcmrmel removes one or more elements from one or more DICOM files

> [!TIP]
> To delete the private tags added by a Philips PACS system you can remove 
> groups 0x07a1, 0x07a3 and 0x07a5 using the command
> `dcmrmel <DIR> --rm-group 0x07a1 0x07a3 0x07a5`

## Installing
1. Create a new virtual environment in which to install `dcmrmel`:

    ```bash
    uv venv dcmrmel-venv
    ```
   
2. Activate the virtual environment:

    ```bash
    source dcmrmel-venv/bin/activate
    ```

4. Install using `uv pip`:
    ```bash
    uv pip install git+https://github.com/SWastling/dcmrmel.git
    ```
   
> [!TIP]
> You can also run `dcmrmel` without installing it using 
>[uvx](https://docs.astral.sh/uv/guides/tools/) i.e. with the command 
>`uvx --from  git+https://github.com/SWastling/dcmrmel.git dcmrmel`

## License
See [MIT license](./LICENSE)


## Authors and Acknowledgements
[Dr Stephen Wastling](mailto:stephen.wastling@nhs.net)

