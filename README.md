# Yiddish texts for training TTS

A collection of Yiddish texts paired with audio recordings

Repo structure:
* `catalog.csv`: A spreadsheet containing bibliographic information and links
* `txt/`: Text files; these will be periodically updated with corrections and moved into `/txt/for_training/`
* `pdf/`: Original PDF versions of the texts

Running `python dl_and_segment.py --download --segment --gen_lexicon --purge` will do the following steps:
1. Download audio files for each of the texts that are marked in the catalog as having been hand-corrected.
2. Use [aeneas](https://www.readbeyond.it/aeneas/) to find the timestamps in the audio corresponding to each sentence in the text, and create segmented audio/text pairs. The texts will be in three versions: `yivo_respelled` (YIVO with precombined Unicode characters, with Hebrew/Aramaic-origin words respelled phonetically); `yivo_original` (YIVO with precombined Unicode chars, no respellings); `hasidic` (a version of `yivo_original` but respelled according to Hasidic orthographic norms, including the removal of all diacritics)
3. Create a lexicon (for each orthography) to be used with the [Montreal Forced Aligner](https://montreal-forced-aligner.readthedocs.io/en/latest/).
4. Purge audio files that are too short to be used with the MFA.
5. Finally, print some commands to the screen to train and run the MFA.

All of the files created by the above steps will be available in an untracked directory called `generated/`. Speaker codes are based on dialects, e.g., `lit1`, `lit2` (for Lithuanian Yiddish), `pol1` (for Polish Yiddish).

Running `bash prep_dataset.sh` will create a publishable TTS dataset (in `generated/dataset/`)
