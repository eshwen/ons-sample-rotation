# -*- coding: utf-8 -*-
"""Rewrite of prepare_sample_frame_2022.py."""

__author__ = "eshwen.bhal@ext.ons.gov.uk"
__version__ = "v1.0"

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path

import pandas as pd


def parse_arguments():
    """Parse CLI arguments.

    Returns:
        argparse.Namespace: Parsed arguments accessible as object attributes.

    """
    parser = ArgumentParser(description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-i", "--infile",
        type=str, default=r"\\nsdata6\pd_gis\Sample Rotation\Sample Rotation 2022\SampleFrame2022.xls",
        help="File to load. Location data exported from ArcMap."
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite the output file(s) if they already exist."
    )

    args = parser.parse_args()
    return args


def merge_facility_ID(df, outfile, overwrite=False):
    """Merge Facility ID of '2' location partners onto their '1' pairs and save.

    Args:
        df (pandas.DataFrame): Locations dataframe.
        outfile (str or pathlib.Path): Path to output file.
        overwrite (bool, optional): Overwrite if the file already exists.

    Returns:
        pandas.DataFrame: Dataframe with merged facility IDs.
    
    """
    suffix_y = "_merge"
    merged = pd.merge(
        df, df[["LocName", "FacilityID", "Merge_ID"]],
        how='left', left_on="Merge_ID", right_on="FacilityID", suffixes=(None, suffix_y)
    )
    merged.drop(columns=[f"Merge_ID{suffix_y}"], inplace=True)
    write_df_to_excel(merged, outfile, overwrite=overwrite)
    return merged


def merge_turnover_outlets(df, outfile, overwrite=False):
    """Merge turnover and number of outlets of donor locations labelled '2' onto acceptor location rows (for locations labelled '1') and save.

    Args:
        df (pandas.DataFrame): Locations dataframe.
        outfile (str or pathlib.Path): Path to output file.
        overwrite (bool, optional): Overwrite if the file already exists.

    Returns:
        pandas.DataFrame: Dataframe with merged facility IDs.

    """
    suffix_y = "_loc2"
    merged = pd.merge(
        df, df[["FacilityID", "Sum_Turnov", "OutletCt"]],
        how='left', left_on="FacilityID_merge", right_on="FacilityID", suffixes=(None, suffix_y)
    )
    merged.drop(columns=["Unnamed: 0", f"FacilityID{suffix_y}"], inplace=True)
    write_df_to_excel(merged, outfile, overwrite=overwrite)
    return merged


def write_df_to_excel(df, outfile, overwrite=False):
    """Write a dataframe to an Excel document.

    Args:
        df (pandas.DataFrame): Dataframe to write.
        outfile (str or pathlib.Path): Path to output file.
        overwrite (bool, optional): Overwrite if the file already exists.

    Raises:
        FileExistsError: If the output file already exists and `overwrite` is `False`.

    """
    out_file = Path(outfile)
    if out_file.exists() and not overwrite:
        raise FileExistsError(f"""The file {outfile} already exists and `overwrite` is False.
Either change the output filename or rerun with `overwrite` as True.""")
    else:
        df.to_excel(out_file)


def postproc_turnover_df(df):
    """Postprocess the dataframe with merged turnovers.

    Args:
        df (pandas.DataFrame): Dataframe to process.

    Returns:
        pandas.DataFrame: Postprocessed dataframe.

    """
    df_copy = df.copy()  # Don't overwrite original df
    # Convert missing values to zero so operations can be performed on them
    df_copy.fillna(0, inplace=True)

    # Perform sums and calculate average turnover per outlet
    df_copy["Total_TURNOV"] = df_copy["Sum_Turnov"] + df_copy["Sum_Turnov_loc2"]
    df_copy["Total_OutletCt"] = df_copy["OutletCt"] + df_copy["OutletCt_loc2"]
    df_copy["avg_TURNOV"] = df_copy["Total_TURNOV"] / df_copy["Total_OutletCt"]  # What was used as the 'size' variable in the PPS sampling
    return df_copy


def save_df_duplicates(df, col, outfile, overwrite=False):
    """Write a dataframe to an Excel document, containing only duplicate rows.

    Args:
        df (pandas.DataFrame): Dataframe to write.
        col (str): Column to check for duplicate values.
        outfile (str or pathlib.Path): Path to output file.
        overwrite (bool, optional): Overwrite if `outfile` already exists.

    """
    duplicates = df.duplicated(col, keep=False)
    write_df_to_excel(df[duplicates], outfile, overwrite=overwrite)


def main(infile, force=False):
    """Runner for script.
   
    Args:
        infile (str): Path to input file.
        force (bool, optional): Overwrite output files if they already exist.

    """
    in_file = Path(infile)
    locations = pd.read_excel(in_file)

    out_file_ID_merge = in_file.parent / "CPI_New_Sampling_Frame_TableToExcel__ID_Merge_2022.xlsx"
    locations_merged = merge_facility_ID(locations, out_file_ID_merge, overwrite=force)

    out_file_turnover_merge = in_file.parent / "CPI_New_Sampling_Frame_TableToExcel__Intermediate_2022.xlsx"
    turnover_merged = merge_turnover_outlets(locations_merged, out_file_turnover_merge, overwrite=force)
    turnover_merged = postproc_turnover_df(turnover_merged)

    # Extra step to check code is running well up until this point
    write_df_to_excel(turnover_merged, in_file.parent / "CPI_New_Sampling_Frame_TableToExcel__Intermediate2_2022.xlsx", overwrite=force)

    # Remove locations with <250 outlets and donor locations (labelled '2') from the sample frame
    turnover_merged = turnover_merged.query("(Total_OutletCt >= 250) & (Merge_Num != 2)")
    write_df_to_excel(turnover_merged, in_file.parent / "CPI_New_Sampling_Frame_Draft_2022.xlsx", overwrite=force)

    # Find those Merge_IDs listed against more than one other location (by mistake) - so they could be reassigned to only one
    save_df_duplicates(turnover_merged, "Merge_ID", in_file.parent / "2022_duplicate_1.xlsx", overwrite=force)
    save_df_duplicates(turnover_merged, "FacilityID_merge", in_file.parent / "2022_duplicate_2.xlsx", overwrite=force)


if __name__ == "__main__":
    args = parse_arguments()
    main(**args.__dict__)
