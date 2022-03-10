# The Reading Electronic Yiddish Documents (REYD) Dataset

The REYD TTS dataset is a speech dataset for Yiddish consisting of 4,892 short audio clips, with a total duration of 475.7 minutes. The recordings are of three speakers, two of whom speak the Lithuanian Yiddish dialect and one who speaks the Polish Yiddish dialect. The source texts are in standard literary Yiddish.

The text sources are mostly works of fiction from the late 19th and early 20th centuries. Audio was recorded at the Montreal Jewish Public Library and the University of Haifa. All source texts and audio are public domain. Permission has been granted by the surviving relatives of the three readers for this work to be made public.

This work has been used to train a TTS system. For an interactive demo and other information, please see our GitHub project page at https://github.com/REYD-TTS. A paper describing the work of assembling this dataset has been submitted for publication and will be linked to on the project page if accepted.

## Directory Structure

Each audio clip has 3 corresponding transcriptions:
- *yivo_orginal* -- Yiddish text in the YIVO standard orthography
- *yivo_respelled* -- as above, but with all Loshn-koydesh words replaced with their phonemic respellings 
- *hasidic* -- where words are respelled (and unpointed) to reflect the orthographic norms of the Hasidic community
 
Each speaker is identified by a speaker ID. These are lit1, lit2 and pol1. The first three letters of the ID represent the dialect of the speaker.

The directory structure is as follows:
```
dataset
├── README.md
├── audio
│   ├── lit1
│   ├── lit2
│   └── pol1
└── text
    ├── hasidic
    │   ├── lit1
    │   ├── lit2
    │   └── pol1
    ├── yivo_original
    │   ├── lit1
    │   ├── lit2
    │   └── pol1
    └── yivo_respelled
        ├── lit1
        ├── lit2
        └── pol1
```
where each text subsubdirectory contains .lab files containing UTF-8 encoded text. Audio subdirectories contain 16 bit PCM encoded .wav files at 44,100Hz.

## Creation

The dataset was prepared using hand-corrected text that was segmented automatically. The results were checked for accuracy. The code used for creating the dataset is available, along with manually corrected source texts, in this repository: https://github.com/REYD-TTS/yiddish-tts-texts

## License

If your use of this work results in a publication being made, we request that you cite the paper listed at https://github.com/REYD-TTS.

## Acknowledgments

None of the three speakers included in this corpus are still alive. We owe a great debt to these readers, who were all lovers of the Yiddish language: to Perec Zylberberg ז"ל, a great believer in the future of Yiddish; to Sara Blacher-Retter ז"ל, a dedicated Israeli nurse; and to Leib Rubinov ז"ל, a lifelong Jewish educator. While the recordings these speakers made were already available to the public online, we have also communicated with their surviving relatives and gathered informed consent in order to publish a corpus and TTS voices based on these recordings.

We thank Mindl Cohen and Amber Kanner Clooney of the Yiddish Book Center, who curated much of the source material and were helpful throughout. Eliezer Niborski provided a digital list of Loshn-koydesh respellings and acted as an independent Yiddish expert evaluator. We also thank Dafna Sheinwald, who connected us with the family of Sara Blacher-Retter, and Refoyl Finkel, for facilitating the correction of Sholem Aleichem's texts and providing additional assistance with OCR.
