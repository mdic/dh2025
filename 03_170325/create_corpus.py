# Import modules for: working on local folders and files; regular expressions; finding files in folder;
# reading JSON files; using BeautifulSoup; working with XML files
import os
import re
from glob import glob
import json
from bs4 import BeautifulSoup
from lxml import etree

# Manually set the 2-letter ISO 3166-1 language code (e.g. English = en), so that only the subtitle files for the set
# language are processed
language_code = re.compile("en.*")

# Create a regular expression to capture the title of the video preceding youtube-dl default naming conventions, where:
# [FILENAME].info.json = the JSON file containing the metadata details
# [FILENAME].[LL].srv3 = the XML file containing the subtitles in SRV3 format, where [LL] is the 2-letter ISO 3166-1 language code
# [FILENAME].[LL].ttml = the XML file containing the subtitles in TTML format, where [LL] is the 2-letter ISO 3166-1 language code
filename_filter = re.compile(
    "(.*?)\.(info\.json|[A-Za-z]{1,3}\.srv3|[A-Za-z]{1,3}\.ttml)"
)
# Create an empty list to store all the video titles
unique_filenames_list = []
# List all filenames present in the folder where the script resides
files = glob("*.*")

# For every single filename found in the folder, do:
for single_file in files:
    # Search for the regular expression for capturing metadata and subtitle files in the filename, and store the result
    # in the 'found_filename' variable
    found_filename = re.search(filename_filter, single_file)
    # If the filename matches the regular expression, extract the filename without the extensions; then check if the cleaned
    # filename is present in the unique_filenames_list, and if not add it
    if found_filename is not None and found_filename[1] not in unique_filenames_list:
        unique_filenames_list.append(found_filename[1])


# Create the function to convert the time-format employed by TTML (HH:MM:SS.MS) into the one employed by SRV3
# (total number of milliseconds); adapted from
# https://stackoverflow.com/questions/59314323/how-to-convert-timestamp-into-milliseconds-in-python
def convert_timestamp(msf):
    hours, minutes, seconds = msf.split(":")
    seconds, milliseconds = seconds.split(".")
    hours, minutes, seconds, milliseconds = map(
        int, (hours, minutes, seconds, milliseconds)
    )
    return (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds


# For each unique filename found do:
for filename in unique_filenames_list:
    # Recreate the full filenames with extensions, and store each one of them into a single variable
    json_file = filename + ".info.json"
    subtitle_files = glob(f"{filename}.*.srv3") + glob(f"{filename}.*.ttml")

    if subtitle_files:
        match = re.search(r'\.([a-zA-Z-]+)\.(srv3|ttml)$', subtitle_files[0])
        language_code = match.group(1) if match else "en"
    else:
        language_code = "en"  # Default fallback if no subtitle file is found

    # 🔹 Now construct filenames dynamically
    srv3_file = f"{filename}.{language_code}.srv3"
    ttml_file = f"{filename}.{language_code}.ttml"
    # srv3_file = filename + "." + language_code + ".srv3"
    # ttml_file = filename + "." + language_code + ".ttml"
    # Create the XML element <text>, root element of the final output
    text_tag = etree.Element("text")

    # Open the metadata JSON file:
    metadata_file = json.loads(open(json_file, encoding="utf-8").read())
    # Add a set of metadata points as attributes of the <text> element tag
    text_tag.attrib["uploader"] = metadata_file["uploader"]
    text_tag.attrib["date"] = metadata_file["upload_date"]
    text_tag.attrib["date_ts"] = str(metadata_file["timestamp"])
    text_tag.attrib["views"] = str(metadata_file["view_count"])
    text_tag.attrib["title"] = metadata_file["fulltitle"]
    # Check if the 'like_count' metadata point is present, if not assign the value "na" to the 'like_count' attribute
    text_tag.attrib["likes"] = str(
        metadata_file["like_count"] if "like_count" in metadata_file else "na"
    )

    # Check if the SRV3 file exists (priority is given to SRV3 over TTML due to the presence of autocaptioning details);
    # if so, do:
    if os.path.isfile(srv3_file):
        # Assign the attribute 'format' with a value of 'srv' to the <text> element tag
        text_tag.attrib["format"] = "srv3"
        # Create the output filename using the input filename
        output_filename = srv3_file + ".xml"
        # Open the SRV3 file
        f = open(srv3_file, "r", encoding="utf-8")
        # Parse its XML contents using BeautifulSoup
        soup = BeautifulSoup(f, features="xml")
        # If the attribute 'ac' (= autocaption) with value '255' is found in the <s> element tag then the subtitles are the result of autocaptioning; hence assign the value 'true' to the variable 'is_ac'. Otherwise assign the value 'false' to 'is_ac'
        if soup.body.find("s", attrs={"ac": True}):
            is_ac = "true"
        else:
            is_ac = "false"

        # Assign the value of 'is_ac' to the <text> element tag attribute 'autocaption'
        text_tag.attrib["autocaption"] = is_ac

        # For each paragraph (i.e. each line of the subtitles) in the file do:
        for sent in soup.body.find_all("p"):
            # Check if the textual content of the paragraph is longer than 1 character; this avoids adding empty paragraphs to the final output
            if len(sent.get_text()) > 1:
                # Create a <p> element tag inside of the XML output
                p_tag = etree.SubElement(text_tag, "p")
                # Add the attribute 'time' (indicating the starting time of the paragraph) and assign it the value appearing in 't'
                p_tag.attrib["time"] = str(sent["t"])
                # Add the attribute 'is_ac' and assign it the value of the previously created variable 'is_ac'
                p_tag.attrib["is_ac"] = is_ac
                p_tag.text = sent.get_text()
            # If the paragraph does not contain any text (i.e. its length is < 1), skip it
            else:
                continue

    # If the SRV3 file does not exists, check if the TTML file does instead; then do (only the steps that differ from the
    # SRV3 procedure are commented):
    elif os.path.isfile(ttml_file):
        text_tag.attrib["format"] = "ttml"
        text_tag.attrib["autocaption"] = "na"
        output_filename = ttml_file + ".xml"
        f = open(ttml_file, "r", encoding="utf-8")
        soup = BeautifulSoup(f, features="xml")

        for sent in soup.body.find_all("p"):
            if len(sent.get_text()) > 1:
                p_tag = etree.SubElement(text_tag, "p")
                # Add the 'time' attribute, assigning it as value the starting time from the 'begin' attribute in the original file,
                # converted into milliseconds using the 'convert_timestamp' function
                p_tag.attrib["time"] = str(
                    convert_timestamp(str(sent["begin"])))
                p_tag.attrib["is_ac"] = "na"
                p_tag.text = sent.get_text()
            else:
                continue
    # If neither the SRV3 nor the TTML files are found, print 'No subtitle files found.'
    else:
        print("No subtitle files found.")

    # Write the extracted data formatted in XML to the final XML structure
    tree = etree.ElementTree(text_tag)
    # Write the XML to the output file
    tree.write(
        output_filename, pretty_print=True, xml_declaration=True, encoding="utf-8"
    )
