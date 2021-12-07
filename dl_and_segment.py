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
import json
import yiddish_text_tools

CATALOGUE_PATH = 'catalog.csv'
AUDIO_PATH = 'audio'
ROM_PATH = 'romanised'
RESPELL_PATH = 'respelled'
HASID_PATH = 'hasidified'
SEGMENTED_PATH = 'segmented'
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
    os.makedirs(RESPELL_PATH, exist_ok=True)
    os.makedirs(HASID_PATH, exist_ok=True)
    os.makedirs('syncmaps', exist_ok=True)
    for _, source in sources.iterrows():
        audio = os.path.join(AUDIO_PATH, Path(source['Filename']).stem + '.mp3')
        if os.path.exists(audio) and source['IsCorrected'] == 'y':
            cropped_audio = os.path.join(AUDIO_PATH, 'cropped_' + Path(source['Filename']).stem + '.mp3')
            if not os.path.exists(cropped_audio):
                print(f'loading audio {audio}')
                waveform = pydub.AudioSegment.from_mp3(audio)
                print(f'loaded audio {audio}')

                if not math.isnan(source['time_start']) and not math.isnan(source['time_end']):
                    # PyDub uses milliseconds for cropping!
                    start_ms = int(float(source['time_start']) * 1000)
                    end_ms = int(float(source['time_end']) * 1000)
                    waveform = waveform[start_ms:end_ms]
                cropped_audio = os.path.join(AUDIO_PATH, 'cropped_' + Path(source['Filename']).stem + '.mp3')
                print(f'saving cropped audio to {cropped_audio}')
                waveform.export(cropped_audio)
            else:
                waveform = pydub.AudioSegment.from_mp3(cropped_audio)

            orig_text = os.path.join(source['Filepath'])
            respelled = os.path.join(RESPELL_PATH, source['Filename'])
            hasidified = os.path.join(HASID_PATH, source['Filename'])
            romanized = os.path.join(ROM_PATH, source['Filename'])
            with open(orig_text) as y_text:
                y_text = y_text.read()
                y_text = clean_punc(y_text)
                respelled_text = yiddish_text_tools.respell_loshn_koydesh(y_text)
                hasidified_text = yiddish_text_tools.hasidify(y_text)
                rom_text = yiddish_text_tools.romanise_german(respelled_text)
            
            with open(respelled, 'w') as text:
                text.write(respelled_text)
            with open(hasidified, 'w') as text:
                text.write(hasidified_text)
            with open(romanized, 'w') as text:
                text.write(rom_text)

            '''
            for i, (y, r) in enumerate(zip(y_text.splitlines(), rom_text.splitlines())):
                print(y, r, '\n\n\n')
            exit()
            '''


            config_string = u"task_language=deu|is_text_type=plain|os_task_file_format=json"
            task = Task(config_string=config_string)
            task.audio_file_path_absolute = cropped_audio
            task.text_file_path_absolute = romanized
            task.sync_map_file_path_absolute = os.path.join('syncmaps', Path(source['Filename']).stem + '.json')
            # process Task
            if not os.path.exists(task.sync_map_file_path_absolute):
                ExecuteTask(task).execute()
                # output sync map to file
                task.output_sync_map_file()
            done_dir = os.path.join(SEGMENTED_PATH, Path(source['Filename']).stem)
            orig_subdir = os.path.join(SEGMENTED_PATH, Path(source['Filename']).stem, 'original') # non-respelled version
            hasidified_subdir = os.path.join(SEGMENTED_PATH, Path(source['Filename']).stem, 'hasidified') # hasidified version
            os.makedirs(done_dir, exist_ok=True)
            os.makedirs(orig_subdir, exist_ok=True)
            os.makedirs(hasidified_subdir, exist_ok=True)
            divide_mp3(waveform, task.sync_map_file_path_absolute, done_dir, respelled_text, orig_subdir, y_text, hasidified_subdir, hasidified_text)

def divide_mp3(mp3_input, json_path, output_dir, respelled_text, orig_subdir, orig_text, hasidified_subdir, hasidified_text):
    with open(json_path) as js_f:
        aeneas_segment = json.load(js_f)
        for i, (line, respelled_line, orig_line, hasidified_line) in enumerate(zip(aeneas_segment["fragments"], respelled_text.splitlines(), orig_text.splitlines(), hasidified_text.splitlines())):
            ms = lambda x: int(1000*float(x))
            start = ms(line['begin'])
            end = ms(line['end'])
            text = line['lines']
            segment = mp3_input[start:end]
            basename = os.path.join(output_dir, f'vz{i:04d}')
            segment.export(basename + '.mp3')
            with open(basename + '.txt', "w") as text_file:
                print(respelled_line, text[0], '\n\n\n\n\n')
                text_file.write(respelled_line)
            
            orig_basename = os.path.join(orig_subdir, f'vz{i:04d}')
            with open(orig_basename + '.txt', "w") as text_file:
                text_file.write(orig_line)
            hasidified_basename = os.path.join(hasidified_subdir, f'vz{i:04d}')
            with open(hasidified_basename + '.txt', "w") as text_file:
                text_file.write(hasidified_line)

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

# fix punctuation spacing
def clean_punc(text):
    text = re.sub(r"\s+([,.:;!?])", r"\1 ", text)
    text = re.sub(r"\s+", r" ", text)
    text = re.sub(r"([.!?]+)", r"\1 \n ", text)
    return text.strip()

if __name__ == '__main__':
    main()
