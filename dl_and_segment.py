import pandas as pd
import wget
import argparse
import shutil
from pathlib import Path
import os
import re
import zipfile
import aeneas
from urllib import parse
import soundfile as sf
import librosa
import pydub
import math

CATALOGUE_PATH = 'catalog.csv'
AUDIO_PATH = 'audio'
ROM_PATH = 'romanised'
SEGMENTED_PATH = 'segmented_audio'
SR = 22050

from aeneas.executetask import ExecuteTask
from aeneas.task import Task

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--download', action='store_true')
    ap.add_argument('--segment', action='store_true')
    args = ap.parse_args()
    sources = pd.read_csv(CATALOGUE_PATH)

    if args.download:
        try:
            download(sources)
        except Exception as my_ex:
            print(my_ex)
            shutil.rmtree('tmp')

    if args.segment:
        segment(sources)

def segment(sources):
    os.makedirs(ROM_PATH, exist_ok=True)
    os.makedirs('syncmaps', exist_ok=True)
    for _, source in sources.iterrows():
        audio = os.path.join(AUDIO_PATH, Path(source['Filename']).stem + '.mp3')
        if os.path.exists(audio) and source['IsCorrected'] == 'y':
            print(f'loading audio {audio}')
            waveform = pydub.AudioSegment.from_mp3(audio)
            print(f'loaded audio {audio}')

            if not math.isnan(source['time_start']) and not math.isnan(source['time_end']):
                # PyDub uses milliseconds for cropping!
                start_ms = int(source['time_start'])*1000
                end_ms = int(source['time_end'])*1000
                waveform = waveform[start_ms:end_ms]
            cropped_audio = os.path.join(AUDIO_PATH, 'cropped_' + Path(source['Filename']).stem + '.mp3')
            waveform.export(cropped_audio)

            text =  os.path.join(source['Filepath'])
            romanized = os.path.join(ROM_PATH, source['Filename'])
            with open(text) as y_text:
                rom_text = romanise(y_text.read())
                print(rom_text)
            with open(romanized, 'w') as r_text:
                r_text.write(rom_text)


            config_string = u"task_language=deu|is_text_type=plain|os_task_file_format=json"
            task = Task(config_string=config_string)
            task.audio_file_path_absolute = cropped_audio
            task.text_file_path_absolute = romanized
            task.sync_map_file_path_absolute = os.path.join('syncmaps', Path(source['Filename']).stem + '.json')
            # process Task
            ExecuteTask(task).execute()
            # output sync map to file
            task.output_sync_map_file()


def download(sources):
    os.makedirs('tmp', exist_ok=True)
    for _, source in sources.iterrows():
        destination = os.path.join(AUDIO_PATH, Path(source['Filename']).stem + '.mp3')
        print(f'Downloading {destination} {source["audio"]}')
        if os.path.exists(destination):
            print(destination + ' already downloaded, skipping')
        else:
            if source['audio'][-3:] == 'mp3':
                try:
                    filename = wget.download(parse.unquote(source['audio']), out='tmp')
                except Exception as exy:
                    my_exy = exy
                    print(my_exy)
                    print(my_exy.geturl())
                    print(source['audio'])

                if zipfile.is_zipfile(filename):
                    zf = zipfile.ZipFile(filename)
                    unzipped = zf.extractall()
                    print(unzipped)
                    exit()
                print(filename)
                shutil.move(filename, destination)
            else:
                pass # TODO pass big zips for now

# TODO this is stolen from /yiddis-tools and must be moved to yiddish text
# tools. Important to get all text tools in the same place
def romanise(text):
    rom = {"א": "",    "אַ": "a", "אָ": "o",
           "ב": "b",   "בּ": "b", "בֿ": "w",
           "ג": "g",
           "ד": "d",
           "ה": "h",
           "ו": "u",   "וּ": "u",
           "װ": "w",
           "ױ": "eu",
           "ז": "s",
           "ח": "ch",
           "ט": "t",
           "י": "i",   "יִ": "i",
           "ײ": "ei",  "ײַ": "ei",
           "כּ": "k",   "כ": "ch", "ך": "ch",
           "ל": "l",
           "מ": "m",   "ם": "m",
           "נ": "n",   "ן": "n",
           "ס": "ss",
           "ע": "e",
           "פּ": "p",   "פֿ": "f",  "פ": "f", "ף": "f",
           "צ": "z",   "ץ": "z",
           "ק": "k",
           "ר": "r",
           "ש": "sch", "שׂ": "ss",
           "תּ": "t",   "ת": "ss"
        }

    output = ""
    for c in text:
        if c in rom.keys():
            output += rom[c]
        else:
            output += c

    output = re.sub(r"־", r"-", output)
    output = re.sub(r"schp", r"sp", output)
    output = re.sub(r"scht([aeiour])", r"st\1", output)
    output = re.sub(r"\bpun\b", r"fun", output)
    output = re.sub(r"eup", r"euf", output)

    return clean_punc(output)

# fix punctuation spacing
def clean_punc(text):
    text = re.sub(r"\s+([,.:;!?])", r"\1 ", text)
    text = re.sub(r"\s+", r" ", text)
    text = re.sub(r"([.!?])", r"\1 \n ", text)
    return text.strip()

if __name__ == '__main__':
    main()
