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
import glob
import subprocess

from yiddish_text_tools import yiddish_text_tools


CATALOGUE_PATH = 'catalog.csv'
PREFIX = 'generated'
pref = lambda path: os.path.join(PREFIX, path) # Put all generated files in a subdir for neatness
os.makedirs(PREFIX, exist_ok=True)
AUDIO_PATH = pref('audio')
SYNCMAPS_DIR = pref('syncmaps')
ROM_PATH = pref('romanised')
RESPELL_PATH = pref('respelled')
HASID_PATH = pref('hasidified')
SEGMENTED_PATH = pref('segmented')
SR = 22050

speaker_codes = {
    'Sara Blacher-Retter' : 'lit1',
    'Leib Rubinov' : 'lit2',
    'Perec Zylberberg' : 'pol1',
}

from aeneas.executetask import ExecuteTask
from aeneas.task import Task

utterance_id = 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--download', action='store_true')
    ap.add_argument('--segment', action='store_true')
    ap.add_argument('--gen_lexicon', action='store_true')
    ap.add_argument('--purge', action='store_true')
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

    if args.gen_lexicon:
        gen_lexicon()

    if args.purge:
        purge_dataset()



def gen_lexicon():
    '''Adapted from Sam Lo's codebase, generates a lexicon for MFA'''
    yivo_respelled_utterances = glob.glob(SEGMENTED_PATH + '/yivo_respelled/*/*.txt')
    yivo_original_utterances = glob.glob(SEGMENTED_PATH + '/yivo_original/*/*.txt')
    hasidified_utterances = glob.glob(SEGMENTED_PATH + '/hasidified/*/*.txt')
    
    unique_words_yivo_respelled = set()
    unique_words_yivo_original = set()
    unique_words_hasidified = set()
    
    for utterance_dir in [yivo_respelled_utterances, yivo_original_utterances, hasidified_utterances]:
        for utterance in utterance_dir:
            with open(utterance) as f:
                text = f.read()
                text = re.sub(r"[^ ־׳״אאַאָבבּבֿגדהווּײװױזחטייִײַכּכךלמםנןסעפּפֿפףצץקרששׂתּת']", r"", text)
                for word in text.split():
                    if utterance_dir == yivo_respelled_utterances:
                        unique_words_yivo_respelled.add(word)
                    elif utterance_dir == yivo_original_utterances:
                        unique_words_yivo_original.add(word)
                    else:
                        unique_words_hasidified.add(word)

    with open(f"{PREFIX}/lexicon_yivo_respelled.txt", "w") as f:
        for i, word in enumerate(sorted(unique_words_yivo_respelled)):
            word_no_punct_shtumer_final = re.sub(r"[־׳״'א\-]", r"", word) # remove punct and shtumer alef from phonetic
            word_no_punct_shtumer_final = re.sub(r"ך", r"כ", word_no_punct_shtumer_final) # remove final forms
            word_no_punct_shtumer_final = re.sub(r"ם", r"מ", word_no_punct_shtumer_final)
            word_no_punct_shtumer_final = re.sub(r"ן", r"נ", word_no_punct_shtumer_final)
            word_no_punct_shtumer_final = re.sub(r"ף", r"פֿ", word_no_punct_shtumer_final)
            word_no_punct_shtumer_final = re.sub(r"ץ", r"צ", word_no_punct_shtumer_final)
            if word_no_punct_shtumer_final:
                f.write(f"{word}\t{' '.join(word_no_punct_shtumer_final)}")
            if i != 0:
                f.write("\n")
                
    with open(f"{PREFIX}/lexicon_yivo_original.txt", "w") as f:
        for i, word in enumerate(sorted(unique_words_yivo_original)):
            word_no_punct_final = re.sub(r"[־׳״'\-]", r"", word) # remove punct from phonetic
            word_no_punct_final = re.sub(r"ך", r"כ", word_no_punct_final) # remove final forms
            word_no_punct_final = re.sub(r"ם", r"מ", word_no_punct_final)
            word_no_punct_final = re.sub(r"ן", r"נ", word_no_punct_final)
            word_no_punct_final = re.sub(r"ף", r"פֿ", word_no_punct_final)
            word_no_punct_final = re.sub(r"ץ", r"צ", word_no_punct_final)
            if word_no_punct_final:
                f.write(f"{word}\t{' '.join(word_no_punct_final)}")
            if i != 0:
                f.write("\n")
                
    with open(f"{PREFIX}/lexicon_hasidified.txt", "w") as f:
        for i, word in enumerate(sorted(unique_words_hasidified)):
            word_no_punct_final = re.sub(r"[־׳״'\-]", r"", word) # remove punct from phonetic
            word_no_punct_final = re.sub(r"ך", r"כ", word_no_punct_final) # remove final forms except fey (b/c non-final fey is ambiguous)
            word_no_punct_final = re.sub(r"ם", r"מ", word_no_punct_final)
            word_no_punct_final = re.sub(r"ן", r"נ", word_no_punct_final)
            word_no_punct_final = re.sub(r"ץ", r"צ", word_no_punct_final)
            if word_no_punct_final:
                f.write(f"{word}\t{' '.join(word_no_punct_final)}")
            if i != 0:
                f.write("\n")


def segment(sources):
    os.makedirs(ROM_PATH, exist_ok=True)
    os.makedirs(RESPELL_PATH, exist_ok=True)
    os.makedirs(HASID_PATH, exist_ok=True)
    os.makedirs(SYNCMAPS_DIR, exist_ok=True)
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


            config_string = u"task_language=deu|is_text_type=plain|os_task_file_format=json"
            task = Task(config_string=config_string)
            task.audio_file_path_absolute = cropped_audio
            task.text_file_path_absolute = romanized
            task.sync_map_file_path_absolute = os.path.join(SYNCMAPS_DIR, Path(source['Filename']).stem + '.json')
            # process Task
            if not os.path.exists(task.sync_map_file_path_absolute):
                ExecuteTask(task).execute()
                # output sync map to file
                task.output_sync_map_file()
            speaker_code = speaker_codes[source['Narrator']]
            audio_subdir = os.path.join(SEGMENTED_PATH, 'audio', speaker_code)
            yivo_respelled_subdir = os.path.join(SEGMENTED_PATH, 'yivo_respelled', speaker_code)
            yivo_orig_subdir = os.path.join(SEGMENTED_PATH, 'yivo_original', speaker_code)
            hasidified_subdir = os.path.join(SEGMENTED_PATH, 'hasidified', speaker_code)
            os.makedirs(audio_subdir, exist_ok=True)
            os.makedirs(yivo_respelled_subdir, exist_ok=True)
            os.makedirs(yivo_orig_subdir, exist_ok=True)
            os.makedirs(hasidified_subdir, exist_ok=True)
            divide_mp3(waveform, task.sync_map_file_path_absolute, audio_subdir, yivo_respelled_subdir, respelled_text, yivo_orig_subdir, y_text, hasidified_subdir, hasidified_text)


def divide_mp3(mp3_input, json_path, audio_subdir, yivo_respelled_subdir, respelled_text, yivo_orig_subdir, orig_text, hasidified_subdir, hasidified_text):
    # Utterance id keeps increasing throughout all the calls to this function
    global utterance_id
    with open(json_path) as js_f:
        aeneas_segment = json.load(js_f)
        texts = zip(
                aeneas_segment["fragments"],
                respelled_text.splitlines(),
                orig_text.splitlines(),
                hasidified_text.splitlines())

        for (line, respelled_line, orig_line, hasidified_line) in texts:
            ms = lambda x: int(1000*float(x))
            start = ms(line['begin'])
            end = ms(line['end'])
            text = line['lines']
            segment = mp3_input[start:end]
            audio_basename = os.path.join(audio_subdir, f'vz{utterance_id:04d}')
            segment.export(audio_basename + '.mp3')
            
            yivo_respelled_basename = os.path.join(yivo_respelled_subdir, f'vz{utterance_id:04d}')
            with open(yivo_respelled_basename + '.txt', "w") as text_file:
                print(respelled_line, text[0], '\n\n\n\n\n')
                text_file.write(respelled_line)

            yivo_orig_basename = os.path.join(yivo_orig_subdir, f'vz{utterance_id:04d}')
            with open(yivo_orig_basename + '.txt', "w") as text_file:
                text_file.write(orig_line)
            hasidified_basename = os.path.join(hasidified_subdir, f'vz{utterance_id:04d}')
            with open(hasidified_basename + '.txt', "w") as text_file:
                text_file.write(hasidified_line)
            utterance_id += 1

def download(sources):
    os.makedirs('tmp', exist_ok=True)
    os.makedirs(AUDIO_PATH, exist_ok=True)
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
                    print('Error downloading ' + my_exy.geturl())
                    print('Skipping...')

                shutil.move(filename, destination)
            else:
                pass # TODO pass big zips for now


def purge_dataset():
    mp3s = glob.glob(SEGMENTED_PATH + '/audio/*/*.mp3')
    count = 0
    for mp3 in mp3s:
        sox_proc = subprocess.Popen(
                ["soxi", "-D", mp3], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True
        )
        stdout, stderr = sox_proc.communicate()
        if stderr.startswith("soxi FAIL formats"):
            length = 0.
        else:
            length = float(stdout.strip())

        if length < 0.5:
            os.remove(mp3)
            count += 1
            print('removed ', mp3)
    print(f'purged {count} utterances out of {len(mp3s)} :)\n')
    print('You can now run:')
    print('    cd generated')
    print('    mfa validate -a segmented/audio segmented/yivo_respelled lexicon_yivo_respelled.txt')
    print('    mfa train -a segmented/audio segmented/yivo_respelled lexicon_yivo_respelled.txt textgrids/yivo_respelled')
    print('Do the same to train the other two orthographies: yivo_original, hasidified')

# fix punctuation spacing
def clean_punc(text):
    text = re.sub(r"[“„]", '"', text) # MFA interprets these quotation marks as word chars
    text = re.sub(r"[―—–]+", "-", text) # replace dashes with hyphen
    text = re.sub(r"׃", ":", text) # replace sof-pasuk character (a mistake!) with colon
    text = re.sub(r"\s+([,.:;!?])", r"\1 ", text)
    text = re.sub(r"\s+", r" ", text)
    text = re.sub(r"([.!?]+)", r"\1 \n ", text)
    return text.strip()

if __name__ == '__main__':
    main()
