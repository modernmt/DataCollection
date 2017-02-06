#!/bin/bash
LANGCODE=en
SCRIPTS=scripts
TCMODEL=truecasemodels/truecase-model.en
/fs/lofn0/buck/cc/scripts/normalize-punctuation.perl $LANGCODE | \
/fs/lofn0/buck/cc/scripts/tokenizer.perl -a -l $LANGCODE | \
/fs/lofn0/buck/cc/scripts/truecase.perl -model ${TCMODEL}
