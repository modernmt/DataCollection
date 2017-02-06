#!/bin/bash
LANGCODE=en
SCRIPTS=scripts
TCMODEL=truecasemodels/truecase-model.en
iconv -c --from UTF-8 --to UTF-8 | \
perl -CSD -pe 's/\x{200B}|\x{FEFF}|\x{FFFF}|\x{FDD3}//g' | \
${SCRIPTS}/strip_markup.perl | \
${SCRIPTS}/remove_email.perl | \
${SCRIPTS}/remove_whitespace.perl | \
${SCRIPTS}/normalize-punctuation.perl $LANGCODE | \
${SCRIPTS}/split-sentences.perl -l $LANGCODE -splitlinebreak | \
${SCRIPTS}/unescape_html.perl | \
${SCRIPTS}/remove_whitespace.perl
