#!/usr/bin/perl -w

binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");

use strict;

while(<STDIN>) {
    chop;
    my $text = $_;
    $text =~ s/[\w\.\-]+\w@[\w\.\-]+\.[\w]+/name\@domain.com/g;
    if ($text !~ /^\s*$/ ) {
        print $text."\n";
    }
}
