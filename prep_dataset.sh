#!/bin/bashs
# This script will generate a publishable TTS dataset of .wav and .lab files

for speaker in lit1 lit2 pol1
do
  echo Processing speaker: $speaker

  mkdir -p generated/dataset/audio/$speaker
  mkdir -p generated/dataset/text/yivo_respelled/$speaker
  mkdir -p generated/dataset/text/yivo_original/$speaker
  mkdir -p generated/dataset/text/hasidic/$speaker
  
  echo Converting segmented .mp3 to .wav: $speaker
  
  for file in generated/segmented/audio/$speaker/*.mp3
  do
    sox "$file" -c 1 -r 44100 "generated/dataset/audio/$speaker/$(basename -s .mp3 "$file").wav"
  done
  
  echo Copying segmented .txt to .lab: $speaker
  
  for file in generated/segmented/yivo_respelled/$speaker/*.txt
  do
    cp "$file" "generated/dataset/text/yivo_respelled/$speaker/$(basename -s .txt "$file").lab"
  done
    
  for file in generated/segmented/yivo_original/$speaker/*.txt
  do
    cp "$file" "generated/dataset/text/yivo_original/$speaker/$(basename -s .txt "$file").lab"
  done
  
  for file in generated/segmented/hasidic/$speaker/*.txt
  do
    cp "$file" "generated/dataset/text/hasidic/$speaker/$(basename -s .txt "$file").lab"
  done
done

echo Copying lexicon files for MFA

mkdir -p generated/dataset/lexicon

cp generated/lexicon_yivo_respelled.txt generated/dataset/lexicon/lexicon_yivo_respelled.txt
cp generated/lexicon_yivo_original.txt generated/dataset/lexicon/lexicon_yivo_original.txt
cp generated/lexicon_hasidic.txt generated/dataset/lexicon/lexicon_hasidic.txt

echo Done!