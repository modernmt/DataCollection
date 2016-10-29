# DataCollection

Collecting data for machine translation training from CommonCrawl is a two-phase process illustrated in the following diagram:

![CommonCrawl process diagram](/common_crawl_process.png?raw=true "CommonCrawl data collection process")

## Phase 1: Language annotation, building a meta-data database and monolingual data extraction

The first phase detects the languages of the web pages contained in the crawl and other meta-data. A database is built from this data that can be accessed via a RESTful web API.

In this phase monolingual data for language model training can be generated. The data for some of the CommonCrawl crawls and some languages can be found on:

* http://statmt.org/ngrams/
* http://www.statmt.org/wmt16/translation-task.html

For more details on the monolingual data see [ModernMT Deliverable 2.1](http://www.modernmt.eu/deliverables/mmt-d2-1-report-on-data-repository/).
 
