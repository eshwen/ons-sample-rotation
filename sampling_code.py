# -*- coding: utf-8 -*-
"""Generate replacement locations for the location boundary review pilot.

Locations are selected probabilistically, with a weight proportional to their turnover.

"""

__author__ = "eshwen.bhal@ext.ons.gov.uk"
__version__ = "v1.0"

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path

import numpy as np
import pandas as pd


def get_random_float(size=1):
    """Get a single, or array of, randomly-generated float.

    Args:
        size (int, optional): The size of the desired array.

    Returns:
        float, or list of float: A single randomly-generated float (if size == 1).
            Otherwise, a numpy array of floats.

    """
    if size == 1:
        return np.random.rand()
    else:
        return np.random.rand(size)


def is_file_excel(filename):
    """Determine whether a file is in Excel format.

    Args:
        filename (pathlib.Path): Path to file.

    Returns:
        bool: True if the file is in Excel format, False if not.

    """
    return any(filename.suffix == ext for ext in [".xls", ".xlsx"])


def load_df(in_file):
    """Load a dataframe from a file.

    Supports reading Excel spreadsheets by inference from the file extension.
    Otherwise assumes it's a CSV.

    Args:
        in_file (pathlib.Path): Path to the file.

    Returns:
        pandas.DataFrame: Loaded dataframe.

    """
    print(f"Loading input file: {in_file}")
    if is_file_excel(in_file):
        return pd.read_excel(in_file)
    else:
        return pd.read_csv(in_file)


def generate_replacement_locations(df, region, n_locations):
    """Randomly generate a set of replacement locations, with probabilities weighted by their turnover.

    Args:
        df (pandas.DataFrame): Dataframe of locations.
        region (str): Region to select on.
        n_locations (int): Number of replacement locations to select.

    Returns:
        pandas.DataFrame: Subset of df containing the replacement locations.

    """
    print(f"Generating {n_locations} replacement locations for {region}...")
    df_copy = df.copy()  # Don't overwrite original
    df_regional = df_copy.loc[df_copy["Region"] == region].reset_index(drop=True)
    total_turnover = df_regional["Sum_Turnov"].sum()

    # Weight locations by their turnover and set of random numbers to select replacements
    df_regional["weight"] = df_regional["Sum_Turnov"] / total_turnover
    rnd_nums = get_random_float(size=len(df_regional))
    df_regional["weight"] *= rnd_nums

    df_regional.sort_values(by="weight", ascending=False, inplace=True, ignore_index=True)
    df_regional.drop(columns=["weight"], inplace=True)
    return df_regional[:n_locations]


def write_df(df, out_file, overwrite=False):
    """Write the output dataframe to a file.

    As with load_df(), the output is saved in Excel format if inferred from the file extension. Otherwise as a CSV.

    Args:
        df (pandas.DataFrame): Dataframe to write.
        out_file (pathlib.Path): Path to output file.
        overwrite (bool, optional): Overwrite the output file if it already exists.

    """
    if not out_file.parent.exists():
        print(f"Output directory {out_file.parent} does not exist. Creating...")
        out_file.parent.mkdir(parents=True)

    if out_file.exists() and not overwrite:
        raise FileExistsError(f"""The output file {args.outfile} already exists and `force` is False.
Either rerun with the `force` option or select a different output filename.""")

    print(f"Writing output file: {out_file}")
    if is_file_excel(out_file):
        df.to_excel(out_file, index=False)
    else:
        df.to_csv(out_file, index=False)


def parse_arguments():
    """Parse CLI arguments.

    Returns:
        argparse.Namespace: Parsed arguments accessible as object attributes.

    """
    parser = ArgumentParser(description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-i", "--infile",
        type=str, default=r"\\nsdata6\pd_gis\Sample Rotation\Sample Rotation 2022\Currentsamplingframe.xlsx",
        help="File to load."
    )
    parser.add_argument(
        "-n", "--n_locations",
        type=int, default=5,
        help="Number of replacement locations to generate."
    )
    parser.add_argument(
        "-o", "--outfile",
        type=str, default=r"\\nsdata6\pd_gis\Sample Rotation\Sample Rotation 2022\2022 Replacement Locations\Replacement locations.xlsx",
        help="Output file path."
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite the output file if it already exists."
    )

    args = parser.parse_args()
    return args


def main(infile, outfile, n_locations=5, force=False):
    """Runner of the script.

    Args:
        infile (str): Input file to load.
        outfile (str): Output file path.
        n_locations (int, optional): Number of replacement locations to generate.
        force (bool, optional): Overwrite the output file if it already exists.

    """
    in_file = Path(infile)
    df = load_df(in_file)
    regions = df["Region"].unique()

    lst_new_locs = []
    for region in regions:
        lst_new_locs.append(generate_replacement_locations(df, region, n_locations))
    df_new_locs = pd.concat(lst_new_locs, ignore_index=True)

    out_file = Path(outfile)
    write_df(df_new_locs, out_file, overwrite=force)


if __name__ == "__main__":
    args = parse_arguments()
    main(**args.__dict__)
