How to collect and prepare bilingual data for dev, test and training

X) Script for preparing bilingual data from DataCloud_Datasets and MyMemory_Datasets 

   $> bash scripts_bilingual/TMX_all_phases.sh en_de|en_fr|en_es


X) Script for preparing bilingual data from PublicData_Datasets, WebData_Datasets, and WebData_ILSP_Datasets

   $> bash scripts_bilingual/TMX_all_phases.sh en_de|en_fr|en_es


How to prepare monolingual data

X) Script for downloading monolingual data from data.statmt.org (UEdin)
 
   For all languages but English
   $> bash scripts_monolingual/get_monolingual_corpus.sh [de|es|fr|it|ru|...]

   For English only
   $> bash scripts_monolingual/get_monolingual_corpus.sh en

X) Script for reducing the size of the monolingual data

   For all languages but English
   $> bash scripts_monolingual/reduce_monolingual_monolingual_corpus.sh [de|es|fr|it|ru|...] 

   For English only
   $> bash scripts_monolingual/reduce_monolingual_corpus_English.sh en

