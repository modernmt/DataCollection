# DataCollection

Collecting data for machine translation training from CommonCrawl is a two-phase process illustrated in the following diagram:

![CommonCrawl process diagram](/common_crawl_process.png?raw=true "CommonCrawl data collection process")

## Phase 1: Language annotation, building a meta-data database and monolingual data extraction

The first phase detects the languages of the web pages contained in the crawl and other meta-data. A database is built from this data that can be accessed via a RESTful web API.

The [metadata documentation](/metadata/metadata.md) describes phase 1 step-by-step.

In this phase monolingual data for language model training can be extracted. The data for some of the CommonCrawl crawls and some languages can be found on:

* http://statmt.org/ngrams/
* http://www.statmt.org/wmt16/translation-task.html

For more details on the monolingual data see [ModernMT Deliverable 2.1](http://www.modernmt.eu/deliverables/mmt-d2-1-report-on-data-repository/).
 
## Phase 2: Extracting parallel data and optional cleaning
 
In the second phase the meta-data collected in phase 1 is used to extract parallel data from CommonCrawl data based on URL pattern matching. Phase 2 is documented step-by-step in the [baseline documentation](/baseline/baseline.md)

For the language pairs en↔it, en↔fr and en↔it matched URL data is available for quick data extraction in release 0.1.0 https://github.com/ModernMT/DataCollection/releases/tag/0.1.0
