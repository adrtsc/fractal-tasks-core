"""
Copyright 2022 (C)
    Friedrich Miescher Institute for Biomedical Research and
    University of Zurich

    Original authors:
    Tommaso Comparin <tommaso.comparin@exact-lab.it>

    This file is part of Fractal and was originally developed by eXact lab
    S.r.l.  <exact-lab.it> under contract with Liberali Lab from the Friedrich
    Miescher Institute for Biomedical Research and Pelkmans Lab from the
    University of Zurich.

Helper functions to address channels via OME-NGFF/OMERO metadata
"""
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Sequence

import zarr


def check_well_channel_labels(*, well_zarr_path: str) -> None:
    """
    Check that the channel labels for a well are unique

    First identify the channel-labels list for each image in the well, then
    compare lists and verify their intersection is empty

    :params well_zarr_path: path to an OME-NGFF well zarr group
    """

    # Iterate over all images (multiplexing cycles, multi-FOVs, ...)
    group = zarr.open_group(well_zarr_path, mode="r+")
    image_paths = [image["path"] for image in group.attrs["well"]["images"]]
    list_of_channel_lists = []
    for image_path in image_paths:
        channels = get_omero_channel_list(
            image_zarr_path=f"{well_zarr_path}/{image_path}"
        )
        list_of_channel_lists.append(channels[:])

    # For each pair of channel-labels lists, verify they do not overlap
    for ind_1, channels_1 in enumerate(list_of_channel_lists):
        labels_1 = set([c["label"] for c in channels_1])
        for ind_2 in range(ind_1):
            channels_2 = list_of_channel_lists[ind_2]
            labels_2 = set([c["label"] for c in channels_2])
            intersection = labels_1 & labels_2
            if intersection:
                hint = (
                    "Are you parsing fields of view into separate OME-Zarr"
                    " images? This could lead to non-unique channel labels"
                    ", and then could be the reason of the error"
                )
                raise ValueError(
                    "Non-unique channel labels\n"
                    f"{labels_1=}\n{labels_2=}\n{hint}"
                )


def get_channel_from_image_zarr(
    *, image_zarr_path: str, label: str = None, wavelength_id: str = None
) -> Dict[str, Any]:
    """
    Extract a channel from OME-NGFF zarr attributes

    This is a helper function that combines ``get_omero_channel_list`` with
    ``get_channel_from_list``.

    :param image_zarr_path: Path to an OME-NGFF image zarr group
    :param label: ``label`` attribute of the channel to be extracted
    :param wavelength_id: ``wavelength_id`` attribute of the channel to be
                          extracted
    :returns: A single channel dictionary
    """
    omero_channels = get_omero_channel_list(image_zarr_path=image_zarr_path)
    channel = get_channel_from_list(
        channels=omero_channels, label=label, wavelength_id=wavelength_id
    )
    return channel


def get_omero_channel_list(*, image_zarr_path: str) -> List[Dict[str, Any]]:
    """
    Extract the list of channels from OME-NGFF zarr attributes

    :param image_zarr_path: Path to an OME-NGFF image zarr group
    :returns: A list of channel dictionaries
    """
    group = zarr.open_group(image_zarr_path, mode="r+")
    return group.attrs["omero"]["channels"]


def get_channel_from_list(
    *, channels: Sequence[Dict], label: str = None, wavelength_id: str = None
) -> Dict[str, Any]:
    """
    Find matching channel in a list

    Find the channel that has the required values of ``label`` and/or
    ``wavelength_id``, and identify its positional index (which also
    corresponds to its index in the zarr array).

    :param channels: A list of channel dictionary, where each channel includes
                     (at least) the ``label`` and ``wavelength_id`` keys
    :param label: The label to look for in the list of channels.
    :param wavelength_id: The wavelength_id to look for in the list of
                          channels.
    :returns: A single channel dictionary
    """

    # Identify matching channels
    if label:
        if wavelength_id:
            matching_channels = [
                c
                for c in channels
                if (
                    c["label"] == label and c["wavelength_id"] == wavelength_id
                )
            ]
        else:
            matching_channels = [c for c in channels if c["label"] == label]
    else:
        if wavelength_id:
            matching_channels = [
                c for c in channels if c["wavelength_id"] == wavelength_id
            ]
        else:
            raise ValueError(
                "get_channel requires at least one in {label,wavelength_id} "
                "arguments"
            )

    # Verify that there is one and only one matching channel
    if len(matching_channels) > 1:
        raise ValueError(f"Inconsistent set of channels: {channels}")
    elif len(matching_channels) == 0:
        raise ValueError(
            f"No channel found in {channels} for {label=} and {wavelength_id=}"
        )

    channel = matching_channels[0]
    channel["index"] = channels.index(channel)
    return channel


def define_omero_channels(
    *,
    channels: Sequence[Dict[str, Any]],
    bit_depth: int,
    label_prefix: str = None,
) -> List[Dict[str, Any]]:
    """
    Prepare the .attrs["omero"]["channels"] attribute of an image group

    :param channels: A list of channel dictionaries (each one must include the
                     ``wavelength_id` key).
    :param bit_depth: bit depth
    :returns: omero_channels
    """

    omero_channels = []
    default_colormaps = ["00FFFF", "FF00FF", "FFFF00"]
    for channel in channels:
        wavelength_id = channel["wavelength_id"]

        channel = get_channel_from_list(
            channels=channels, wavelength_id=wavelength_id
        )

        try:
            label = channel["label"]
        except KeyError:
            default_label = wavelength_id
            if label_prefix:
                default_label = f"{label_prefix}_{default_label}"
            logging.warning(
                f"Missing label for {channel=}, using {default_label=}"
            )
            label = default_label

        # Set colormap. If missing, use the default ones (for the first three
        # channels) or gray
        colormap = channel.get("colormap", None)
        if colormap is None:
            try:
                colormap = default_colormaps.pop()
            except IndexError:
                colormap = "808080"

        omero_channels.append(
            {
                "label": label,
                "wavelength_id": wavelength_id,
                "active": True,
                "coefficient": 1,
                "color": colormap,
                "family": "linear",
                "inverted": False,
                "window": {
                    "min": 0,
                    "max": 2**bit_depth - 1,
                },
            }
        )

        try:
            omero_channels[-1]["window"]["start"] = channel["start"]
            omero_channels[-1]["window"]["end"] = channel["end"]
        except KeyError:
            pass

    # Check that channel labels are unique for this image
    labels = [c["label"] for c in omero_channels]
    if len(set(labels)) < len(labels):
        raise ValueError(f"Non-unique labels in {omero_channels=}")

    return omero_channels
