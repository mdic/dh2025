# Import modules for: regular expressions; reading timestamps as date objects; loading files using regular expression;
# generate random numbers; reading JSONL files; working with XML files
import re
from datetime import datetime
from glob import glob
from random import randint
import jsonlines
from lxml import etree

# List all filenames with the .jsonl extension
files = glob("*.jsonl")

# For each file do:
for file in files:
    # Create the root <text> element tag
    text_tag = etree.Element("text")
    # Generate and assign a random number as attribute 'id' of the <text> element tag
    text_tag.attrib["id"] = str(randint(0, 100000))
    # Create the output filename using the original one and substituting '.jsonl' with '.xml'
    output_filename = file.replace("*.jsonl", "") + ".xml"
    print(output_filename)
    # Read the file as a jsonlines one:
    with jsonlines.open(file) as comments:
        # For each line (i.e. metadata data-points for one comment) do:
        for comment in comments:
            # Create a <comment> element tag to enclose the comment
            comment_tag = etree.SubElement(text_tag, "comment")
            # Extract the comment id ('cid') and save it to a variable
            comment_id = str(comment["cid"])
            # Check if the 'cid' contains a full stop character. If so, the comment is a reply to another comment: take the string on
            # the left of the full stop and assign it as value of the attribute 'comment_id', then the string on the right and assign
            # it as value of the attribute 'comment_reply_to' to preserve the original hierarchical structure
            if re.search("(.*?)\.(.*)", comment_id) is not None:
                comment_tag.attrib["comment_id"] = str(
                    re.search("(.*?)\.(.*)", comment_id).group(2)
                )
                comment_tag.attrib["comment_reply_to"] = str(
                    re.search("(.*?)\.(.*)", comment_id).group(1)
                )
            # If there is no full stop character, assign the 'comment_id' as value of the <comment> attribute 'comment_id' and the
            # value 'na' to the 'comment_reply_to' attribute
            else:
                comment_tag.attrib["comment_id"] = comment_id
                comment_tag.attrib["comment_reply_to"] = "na"

            # Extract other metadata data-points and assign them to a set of attributes of the <comment> element tag
            comment_tag.attrib["username"] = str(comment["author"])
            comment_tag.attrib["votes"] = str(comment["votes"])
            comment_tag.attrib["heart"] = str(comment["heart"])
            # Read the Unix timestamp from the metadata data-point 'time_parsed' and convert it into a human-readable datetime object,
            # then store it into the 'comment_date' variable
            comment_date = datetime.fromtimestamp(comment["time_parsed"])
            # Format the time at which the message was posted into the format HHMM (hours and minutes)
            comment_date_time = comment_date.strftime("%H%M")
            # Assign the date elements to different metadata attributes
            comment_tag.attrib["date_d"] = str(comment_date.day)
            comment_tag.attrib["date_m"] = str(comment_date.month)
            comment_tag.attrib["date_y"] = str(comment_date.year)
            comment_tag.attrib["date_time"] = str(comment_date_time)

            # At last, write the content of the comment as the text value of the <comment> element tag
            comment_tag.text = str(comment["text"])

    # Write the extracted data formatted in XML to the final XML structure
    tree = etree.ElementTree(text_tag)
    # Write the XML to the output file
    tree.write(
        output_filename, pretty_print=True, xml_declaration=True, encoding="utf-8"
    )
