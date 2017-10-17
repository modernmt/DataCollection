# DataCollection

Collecting data for machine translation training from CommonCrawl is a two-phase process illustrated in the following diagram:

![CommonCrawl process diagram](/common_crawl_process.png?raw=true "CommonCrawl data collection process")

## Phase 1: Language annotation, building a meta-data file and monolingual data extraction

The first phase detects the languages of the web pages contained in the crawl and other meta-data. A meta-data file is built from this analysis.

The [metadata documentation](/metadata/metadata.md) describes phase 1 step-by-step.

With data from this phase monolingual data for language model training can be extracted. The data for most of the CommonCrawl crawls and many languages can be found on:

* http://statmt.org/ngrams/
* http://www.statmt.org/wmt16/translation-task.html


## Phase 2: Extracting parallel data and optional cleaning
 
In the second phase the meta-data collected in phase 1 is used to extract parallel data from CommonCrawl data based on URL pattern matching. Phase 2 is documented step-by-step in the [baseline documentation](/baseline/baseline.md)

For the language pairs en↔de, en↔fr, en↔es, en↔it, en↔pt, en↔nl and en↔ru matched URL data for CommonCrawl 2015_32 is available for data extraction in [release 0.1.0](https://github.com/ModernMT/DataCollection/releases/tag/0.1.0)
